#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]
	then
	  echo "Requires python file name as argument"
	  exit
fi

for hostname in lecun bengio hawkins hebb hinton hoff  norman pitts;
do
    echo Killing run_${1}.py
    ssh ${hostname} "pkill -9 -f -c run_${1}.py"

echo
done