#!/usr/bin/env bash


pwd=$(cat ../../.sudo_pwd)
for hostname in lecun bengio hawkins hebb hinton hoff  norman pitts;
do
    echo ${hostname}:

    ssh ${hostname} "echo ${pwd} | sudo -S pip3 install pandas==0.23.4"

echo
done

# use --yes flag to skip confirmation when uninstalling via pip