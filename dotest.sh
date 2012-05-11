#!/bin/sh
set -x

killall bluetoothd
killall hcidump

./src/bluetoothd -P input -n &> log &
sleep 10
/usr/sbin/hcidump -x > dump &
/usr/local/sbin/hciconfig hci0 class 0x02540
/usr/local/sbin/hciconfig hci0 piscan
python test/simple-agent

