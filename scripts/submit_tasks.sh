#!/usr/bin/env bash

APPNAME='pytorchtest'
FILESERVERNAME='s76'

# rsync python source code to file-server
rsync --verbose --stats ../src/*.py ${FILESERVERNAME}:/home/lab/cluster/celery/${APPNAME}/src
rsync --verbose --stats ../client.py ../src ${FILESERVERNAME}:/home/lab/cluster/celery/${APPNAME}
rsync --verbose --stats ../app.py ../src ${FILESERVERNAME}:/home/lab/cluster/celery/${APPNAME}

# submit tasks to workers
ssh ${FILESERVERNAME} <<- EOF
    cd /home/lab/cluster/celery/${APPNAME}
    python3 client.py
EOF

# start flower (browser interface to view queue stats)
ssh ${FILESERVERNAME} <<- EOF
    cd /home/lab/cluster/celery/${APPNAME}
    nohup flower -A app --port=5001 > /dev/null 2>&1 &
EOF