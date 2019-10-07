#!/usr/bin/env bash


for hostname in bengio hebb hinton hoff norman pitts hawkins;  # TODO yash is using lecun
do
    echo Uploading watcher to ${hostname}

    echo "Syncing source code"
    scp ../watcher.py ${hostname}:/var/sftp/Ludwig/watcher.py
    scp -r  ../ludwig ${hostname}:/var/sftp/Ludwig

    echo "Killing active jobs"
    ssh ${hostname} 'pkill -u ph'

    echo "Killing active watcher"
    ssh ${hostname} 'pkill --full --echo "python3 watcher.py"'

    echo "Removing stdout file if it exists"
    test -e /media/research_data/stdout/${hostname}.out && rm /media/research_data/stdout/${hostname}.out || echo "file not found"

    echo "Starting new watcher"
    ssh ${hostname} "cd /var/sftp/Ludwig; nohup python3 watcher.py > /media/research_data/stdout/${hostname}.out 2>&1 &"
echo
done
