#!/bin/sh

#Referencing this: https://stackoverflow.com/questions/4377109/shell-script-execute-a-python-program-from-within-a-shell-script
# https://stackoverflow.com/questions/5789642/how-to-send-controlc-from-a-bash-script
# https://stackoverflow.com/questions/5789642/how-to-send-controlc-from-a-bash-script
# https://stackoverflow.com/questions/45494598/how-to-find-the-pid-of-a-running-command-in-bash
# https://www.w3schools.com/bash
# https://stackoverflow.com/questions/28549641/run-multiple-python-scripts-concurrently
# https://stackoverflow.com/questions/2493642/how-can-a-linux-unix-bash-script-get-its-own-pid
# https://stackoverflow.com/questions/45494598/how-to-find-the-pid-of-a-running-command-in-bash
# https://stackoverflow.com/questions/2237080/how-to-compare-strings-in-bash
# https://www.tutorialkart.com/bash-shell-scripting/bash-or/

#Help
check_for_help=$1

if [[ "$check_for_help" == "-h" || "$check_for_help" == "--help" || "$check_for_help" == "" ]]; then
    printf "\n\nERROR: This script should be in this form: ./power-latency_script.sh sample_rate model_name output_file1.csv output_file2.csv\n"
    echo "Ex: ./power-latency_script.sh 1 moondream:latest poweranalysis.csv latency.csv"
    echo "sample_rate: in seconds"
    printf "output_file: must be .csv\n\n"

    kill $$
fi

SECONDS=0

#20 below stands for 20 minutes
python power_analysis.py $1 20 $3 &
PID_power=$!
python VLM_LiveVideo_Prompting_Latency_NANO.py $2 $4 &
PID_latency=$!

duration=$SECONDS

while [ $duration -lt 1200 ]; do
    duration=$SECONDS
    echo "Waiting. At : $((duration)) seconds"
done

PID_origin=$$

echo "terminating power_analysis.py"
kill $PID_power
echo "terminating VLM_LiveVideo_Prompting_Latency_NANO.py"
kill $PID_latency

echo "script ellapsed 20 minutes, terminated scripts"
kill $PID_origin