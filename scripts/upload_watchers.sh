#!/usr/bin/env bash



for hostname in bengio hawkins hebb hinton hoff lecun norman pitts;
#for hostname in bengio;
do
    echo Uploading watcher to ${hostname}

    scp ../watcher.py ${hostname}:/var/sftp/LudwigCluster/watcher.py
    scp ../ludwigcluster/config.py ${hostname}:/var/sftp/LudwigCluster/ludwigcluster/config.py

    echo Killing active watchers
    pkill --full --echo "python3 watcher.py"
    echo Starting watcher
    ssh ${hostname} "cd /var/sftp/LudwigCluster; nohup python3 watcher.py > watcher.out 2>&1 &"
#    ssh ${hostname} "cd /var/sftp/LudwigCluster; python3 watcher.py"
echo
done