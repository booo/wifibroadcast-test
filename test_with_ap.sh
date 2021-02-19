
mode=${1}

SLEEPTIME=20
read up rest </proc/uptime; start="${up%.*}${up#*.}"

if [ ${mode} == "tx" ]; then
        uci set wireless.ap.disabled=1 && wifi && sleep 5 &&
	iw dev mon0 set channel 2 5Mhz && iw dev mon0 set channel 3 5Mhz &  # fucking shit
fi
sleep ${SLEEPTIME}

read up rest </proc/uptime; end="${up%.*}${up#*.}"
runtime=$((10*(${end}-${start})))
echo "AP testmode waittime: ${runtime}"

./test.sh testids.csv ${mode}

if [ ${mode} == "tx" ]; then
        uci set wireless.ap.disabled=0 && uci commit && wifi &
fi

