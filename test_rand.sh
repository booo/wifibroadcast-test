INTERFACE="wlan0"
BREAK=1
WARM_UP=2
WORK_TIME=4
CHANNEL=11

mode=${2}

while IFS=, read -r testid FEC_d FEC_r mcs Txpower stbc ldpc bandwidth
do
    start=$(($(date +%s%N) / 1000000))
    read up rest </proc/uptime; start="${up%.*}${up#*.}"
    
    echo "Starting test testid: ${testid} fec_d: ${FEC_d} fec_r: ${FEC_r} mcs: ${mcs} txpower: ${Txpower} stbc: ${stbc} ldpc: ${ldpc} bandwidth: ${bandwidth}"
    
    #setup interface
    iw dev ${INTERFACE} set channel ${CHANNEL} ${bandwidth}MHz &
    
    if [ ${mode} == "tx" ]; then
      # wait for the rx to start listening
      sleep $((${BREAK} + ${WARM_UP}))
      # Spawn a child process:
      (cat /dev/zero | tx -r ${FEC_r} -b ${FEC_d} ${INTERFACE}) &
      pid=$!
      echo ${pid}
      sleep ${WORK_TIME} 
      #kill -9 ${pid}
      killall tx
      # buffer for rx
      sleep $((${BREAK} + ${WARM_UP}))
    else
      echo "starting receiver"
      sleep ${BREAK}
      #TODO add date to file name
      (./rx -r ${FEC_r} -b ${FEC_d} ${INTERFACE} > "/tmp/searchwing-${testid}.data") & pid=$!
      (tcpdump -i ${INTERFACE} -w "/tmp/searchwing-tcpdump-${testid}.pcap") & tcpdump_pid=$!
      #TODO save debug script output
      sleep $((${WORK_TIME} + ${WARM_UP} + ${WARM_UP}))
      #(./rx_status_test > /tmp/searchwing-debug-${testid}.txt) &
      kill -9 $pid
      kill -9 $tcpdump_pid
      sleep ${BREAK}
    fi
    end=$(($(date +%s%N)/1000000))
    read up rest </proc/uptime; end="${up%.*}${up#*.}"
    echo ${end} ${start}
    runtime=$((10*(${end}-${start})))
    echo "Runtime: ${runtime}"

done < ${1}
