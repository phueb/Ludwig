#!/usr/bin/env bash


pwd=$(cat ../../.sudo_pwd)
for hostname in lecun bengio hawkins hebb hinton hoff  norman pitts;
do
    echo ${hostname}:

    ssh ${hostname} "echo ${pwd} | sudo -S pip3 -h"



echo
done