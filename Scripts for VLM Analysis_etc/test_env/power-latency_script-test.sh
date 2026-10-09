#!/bin/sh

#Referencing this: https://stackoverflow.com/questions/4377109/shell-script-execute-a-python-program-from-within-a-shell-script
# https://stackoverflow.com/questions/5789642/how-to-send-controlc-from-a-bash-script
# https://stackoverflow.com/questions/5789642/how-to-send-controlc-from-a-bash-script
# https://stackoverflow.com/questions/45494598/how-to-find-the-pid-of-a-running-command-in-bash
# https://www.w3schools.com/bash
# https://stackoverflow.com/questions/28549641/run-multiple-python-scripts-concurrently
# https://stackoverflow.com/questions/2493642/how-can-a-linux-unix-bash-script-get-its-own-pid
# https://stackoverflow.com/questions/45494598/how-to-find-the-pid-of-a-running-command-in-bash

#Below is test

SECONDS=0

python test1.py &
PID_power=$!
python test2.py &
PID_latency=$!

duration=$SECONDS

while [ $duration -lt 5 ]; do
    duration=$SECONDS
    echo "Waiting. At : $((duration)) seconds"
done

PID_origin=$$

kill $PID_power
kill $PID_latency

echo "script ellapsed 5 seconds, terminating scripts"
kill $PID_origin