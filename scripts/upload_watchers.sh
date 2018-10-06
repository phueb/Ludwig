#!/usr/bin/env bash

PROJECT_NAME='LudwigCluster'


#for hostname in bengio hawkins hebb hinton hoff lecun norman pitts;
for hostname in bengio hawkins hebb hinton hoff norman pitts;
do
    echo Uploading watcher to ${hostname}

    scp ../watcher.py ${hostname}:/var/sftp/${PROJECT_NAME}/watcher.py
    scp ../src/__init__.py ${hostname}:/var/sftp/${PROJECT_NAME}/src/__init__.py
    scp ../src/config.py ${hostname}:/var/sftp/${PROJECT_NAME}/src/config.py
    echo Killing active watchers
    pkill --full --echo "python3 watcher.py"
    echo Starting watcher
    ssh ${hostname} "cd /var/sftp/${PROJECT_NAME}; nohup python3 watcher.py > watcher.out 2>&1 &"
echo
done