INTERFACE="mon0 mon1"
DATA_DIR="/root/foo/searchwing-wifibroadcast-test"
WFB_DIR="/usr/bin/"
BREAK=1
WARM_UP=2
WORK_TIME=30

mode=${2}
mkdir -p ${DATA_DIR}
ifs=$(echo $INTERFACE | tr " " "\n")

first=1
while IFS=, read -r testid FEC_d FEC_r mcs Txpower stbc ldpc bandwidth mtu channel
do
    read up rest </proc/uptime; start="${up%.*}${up#*.}"
    if [ ${first} == 1 ]; then
	first=0
        continue
    fi

    echo "Starting test testid: ${testid} fec_d: ${FEC_d} fec_r: ${FEC_r} mcs: ${mcs} txpower: ${Txpower} stbc: ${stbc} ldpc: ${ldpc} bandwidth: ${bandwidth} mtu ${mtu} channel: ${channel}"

    for if in ${ifs}
    do
       iw dev ${if} set monitor otherbss fcsfail &
       iw dev ${if} set channel ${channel} ${bandwidth} &
    done

    #setup interface
    if [ ${mode} == "tx" ]; then
      echo "starting transmitter"
      # wait for the rx to start listening
      sleep $((${BREAK} + ${WARM_UP}))
      # Spawn a child process:
      (cat /dev/zero | ${WFB_DIR}/tx -i ${mcs} -r ${FEC_r} -b ${FEC_d} -c ${stbc} -l ${ldpc} -f ${mtu} ${INTERFACE}) &
      sleep ${WORK_TIME}
      killall tx &
      # buffer for rx
      sleep $((${BREAK} + ${WARM_UP}))
    else
      echo "starting receiver"
      sleep ${BREAK}

      for if in ${ifs}
      do
         (tcpdump -i ${if} -w "${DATA_DIR}/searchwing-tcpdump-mon0-${testid}.pcap") & tcpdump_pid=$!
      done
      (mkdir -p "${DATA_DIR}/${testid}-ieee80211" && cp -r /sys/kernel/debug/ieee80211 "${DATA_DIR}/${testid}-ieee80211/start") &
      (${WFB_DIR}/rx -r ${FEC_r} -b ${FEC_d} ${INTERFACE} > "${DATA_DIR}/searchwing-${testid}.data") & pid=$!
      (${WFB_DIR}/rx_status_csv -f "${DATA_DIR}/searchwing-debug-${testid}.csv") &
      sleep $((${WORK_TIME} + ${WARM_UP} + ${WARM_UP}))
      (cp -r /sys/kernel/debug/ieee80211 "${DATA_DIR}/${testid}-ieee80211/end") &
      killall rx &
      killall tcpdump &
      killall rx_status_csv &
      sleep ${BREAK}
    fi
    read up rest </proc/uptime; end="${up%.*}${up#*.}"
    runtime=$((10*(${end}-${start})))
    echo "Runtime: ${runtime}"

done < ${1}

