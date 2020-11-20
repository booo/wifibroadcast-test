INTERFACE="wlan0"
DATA_DIR="/tmp/searchwing-wifibroadcast-test"
WFB_DIR="/usr/bin/"
BREAK=1
WARM_UP=2
WORK_TIME=4
CHANNEL=11

mode=${2}

mkdir -p ${DATA_DIR}

while IFS=, read -r testid FEC_d FEC_r mcs Txpower stbc ldpc bandwidth
do
    read up rest </proc/uptime; start="${up%.*}${up#*.}"

    echo "Starting test testid: ${testid} fec_d: ${FEC_d} fec_r: ${FEC_r} mcs: ${mcs} txpower: ${Txpower} stbc: ${stbc} ldpc: ${ldpc} bandwidth: ${bandwidth}"

    #setup interface
    iw dev ${INTERFACE} set channel ${CHANNEL} ${bandwidth} &

    if [ ${mode} == "tx" ]; then
      echo "starting transmitter"
      # wait for the rx to start listening
      sleep $((${BREAK} + ${WARM_UP}))
      # Spawn a child process:
      (cat /dev/zero | ${WFB_DIR}/tx -i ${mcs} -r ${FEC_r} -b ${FEC_d} ${INTERFACE}) &
      sleep ${WORK_TIME}
      killall tx
      # buffer for rx
      sleep $((${BREAK} + ${WARM_UP}))
    else
      echo "starting receiver"
      sleep ${BREAK}
      (tcpdump -i ${INTERFACE} -w "${DATA_DIR}/searchwing-tcpdump-${testid}.pcap") & tcpdump_pid=$!
      (${WFB_DIR}/rx -r ${FEC_r} -b ${FEC_d} ${INTERFACE} > "${DATA_DIR}/searchwing-${testid}.data") & pid=$!
      (${WFB_DIR}/rx_status_csv -f "${DATA_DIR}/searchwing-debug-${testid}.csv") &
      sleep $((${WORK_TIME} + ${WARM_UP} + ${WARM_UP}))
      killall rx
      killall tcpdump
      killall rx_status_csv
      sleep ${BREAK}
    fi
    read up rest </proc/uptime; end="${up%.*}${up#*.}"
    runtime=$((10*(${end}-${start})))
    echo "Runtime: ${runtime}"

done < ${1}
