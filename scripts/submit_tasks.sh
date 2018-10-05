#!/usr/bin/env bash

APPNAME='pytorchtest'
PATH_TO_SHARE='/media/lab'

# rsync python source code to file-server
rsync --verbose --stats ../src/*.py ${PATH_TO_SHARE}/cluster/celery/${APPNAME}/src
rsync --verbose --stats ../client.py ../src ${PATH_TO_SHARE}/cluster/celery/${APPNAME}
rsync --verbose --stats ../app.py ../src ${PATH_TO_SHARE}/cluster/celery/${APPNAME}

# submit tasks to workers
cd ${PATH_TO_SHARE}/cluster/celery/${APPNAME}
python3 client.py