#!/usr/bin/env bash

HOSTNAME="${COLLECTD_HOSTNAME:-`hostname -f`}"
#INTERVAL="${COLLECTD_INTERVAL:-1}"
INTERVAL=1
SENSORS="tank ambient"

while sleep "$INTERVAL"; do
  for SENSOR in $SENSORS; do
    TEMP=`shuf -i 65-75 -n 1`
    echo "PUTVAL $HOSTNAME/brewme-$SENSOR/gauge-temperature interval=$INTERVAL N:$TEMP"
  done
done
