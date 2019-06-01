#!/usr/bin/env bash

if [[ "$#" -ne 1 ]]
	then
	  echo "Requires python file name as argument"
	  exit
fi


for hostname in bengio hebb hinton hoff norman pitts hawkins;  # TODO yash is using lecun
do
    echo Killing run_${1}.py on ${hostname}
    ssh ${hostname} "pkill -9 -f -c run_${1}.py"

echo
done
