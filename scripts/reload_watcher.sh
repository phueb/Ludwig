#!/usr/bin/env bash

pwd=$(cat ../../.sudo_pwd)
for hostname in bengio hebb hinton hoff norman pitts hawkins;  # TODO yash is using lecun
do
    echo Uploading watcher to ${hostname}

    scp ../watcher.py ${hostname}:/var/sftp/LudwigCluster/watcher.py
    scp ../ludwigcluster/config.py ${hostname}:/var/sftp/LudwigCluster/ludwigcluster/config.py

    echo Killing active watcher
    ssh ${hostname} 'pkill --full --echo "python3 watcher.py"'

    echo Removing stdout file
    rm /media/lab/stdout/${hostname}.out

    # make sure that /media/lab is mounted (not mounted after reboot)
    echo Mounting /media/lab
    ssh ${hostname} "echo ${pwd} | sudo -S mount /media/lab"

    echo Starting new watcher
    ssh ${hostname} "cd /var/sftp/LudwigCluster; nohup python3 watcher.py > /media/lab/stdout/${hostname}.out 2>&1 &"
echo
done
