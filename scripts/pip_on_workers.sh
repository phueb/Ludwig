#!/usr/bin/env bash


pwd="PASSWORD HERE"
for hostname in lecun bengio hawkins hebb hinton hoff norman pitts;
do
    echo ${hostname}:

    ssh ${hostname} "echo ${pwd} | sudo -S pip3.7 install torch numpy tensorflow-gpu==2.0.0rc1"

echo
done

# use --yes flag to skip confirmation when uninstalling via pip