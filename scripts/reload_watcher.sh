#!/usr/bin/env bash


for hostname in bengio hawkins hebb hinton hoff norman pitts;  # TODO yash is using lecun
do
    echo Uploading watcher to ${hostname}

    scp ../watcher.py ${hostname}:/var/sftp/LudwigCluster/watcher.py
    scp ../ludwigcluster/config.py ${hostname}:/var/sftp/LudwigCluster/ludwigcluster/config.py

    echo Killing active watcher
    ssh ${hostname} 'pkill --full --echo "python3 watcher.py"'

    echo Removing stdout file
    rm /media/lab/stdout/${hostname}.out

    echo Starting new watcher
    ssh ${hostname} "cd /var/sftp/LudwigCluster; nohup python3 watcher.py > /media/lab/stdout/${hostname}.out 2>&1 &"
echo
done