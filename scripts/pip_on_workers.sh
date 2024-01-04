#!/usr/bin/env bash


pwd="pwd"
for hostname in bengio hawkins hebb hinton hoff norman pitts lecun;
do
    echo ${hostname}:

    ssh ${hostname} "echo ${pwd} | sudo -H python3.7 -m pip install watchdog"
#    ssh ${hostname} "echo ${pwd} | sudo -H apt-get install nvidia-418 -y "

echo
done

# use --yes flag to skip confirmation when uninstalling via pip