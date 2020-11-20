INTERFACE="wlan0"
BREAK=1
WARM_UP=2
WORK_TIME=4

mode=${2}

while IFS=, read -r testid fec_d fec_r bitrate txpower
do
    start=$(($(date +%s%N) / 1000000))
    read up rest </proc/uptime; start="${up%.*}${up#*.}"
    echo "Starting test testid: ${testid} fec_d: ${fec_d} fec_r: ${fec_r} bitrate: ${bitrate} txpower: ${txpower}"
    if [ ${mode} == "tx" ]; then
      # wait for the rx to start listening
      sleep $((${BREAK} + ${WARM_UP}))
      # Spawn a child process:
      (cat /dev/zero | tx -r ${fec_r} -b ${fec_d} ${INTERFACE}) &
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
      (./rx -r ${fec_r} -b ${fed_d} ${INTERFACE} > "/tmp/searchwing-${testid}.data") & pid=$!
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
