#!/usr/bin/env bash


pwd=$(cat ../../.sudo_pwd)
for hostname in lecun bengio hawkins hebb hinton hoff norman pitts;
do
    echo ${hostname}:

    ssh ${hostname} "cd /var/sftp; echo ${pwd} | sudo -S rm -R Ludwig"
    ssh ${hostname} "cd /var/sftp; echo ${pwd} | sudo -S git clone https://github.com/phueb/Ludwig.git"
    ssh ${hostname} "cd /var/sftp; echo ${pwd} | sudo -S chown -R root:adm Ludwig"
    ssh ${hostname} "cd /var/sftp; echo ${pwd} | sudo -S chmod 770 Ludwig"

echo
done