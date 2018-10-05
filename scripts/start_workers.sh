#!/usr/bin/env bash

APPNAME='pytorchtest'

# kill workers
for i in bengio hawkins hebb hinton hoff lecun norman pitts;
do
    echo Killing worker on $i
    ssh $i <<- 'EOF'
        ps auxww | grep "celery worker" | awk '{print $2}' | xargs kill -9
EOF
done

# start workers
for i in hoff norman hebb hinton pitts hawkins lecun bengio;
do
    echo Starting worker on $i
    ssh $i <<- EOF
        export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:/usr/local/cuda-8.0/lib64"
        export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:/usr/local/cuda-8.0/extras/CUPTI/lib64"
        export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:/usr/local/cuda-8.0/lib64"
        cd /media/lab/cluster/celery/${APPNAME}
        nohup celery worker -l info -A app --concurrency 1 > /media/lab/cluster/logs/${APPNAME}/\$(hostname)_log.txt 2>&1 &
EOF
done