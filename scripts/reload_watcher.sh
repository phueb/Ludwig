#!/usr/bin/env bash

pwd=$(cat ../../.sudo_pwd)
for hostname in bengio hebb hinton hoff norman pitts hawkins;  # TODO yash is using lecun
do
    echo Uploading watcher to ${hostname}

    scp ../watcher.py ${hostname}:/var/sftp/LudwigCluster/watcher.py
    scp ../ludwigcluster/config.py ${hostname}:/var/sftp/LudwigCluster/ludwigcluster/config.py

    echo "Killing active watcher"
    ssh ${hostname} 'pkill --full --echo "python3 watcher.py"'

    echo "Removing stdout file if it exists"
    test -e /media/research_data/stdout/${hostname}.out && rm /media/research_data/stdout/${hostname}.out || echo "file not found"

    # make sure that /media/research_data is mounted (not mounted after reboot)
#    echo "Mounting /media/research_data"
#    ssh ${hostname} "echo ${pwd} | sudo -S mount /media/research_data"

    echo "Starting new watcher"
    ssh ${hostname} "cd /var/sftp/LudwigCluster; nohup python3 watcher.py > /media/research_data/stdout/${hostname}.out 2>&1 &"
echo
done
