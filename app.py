"""
This is the celery application.
Celery is a distributed task queue.
The queue enables users to submit tasks that are executed when compute resources are available.
The celery app defines a set of tasks that a worker can do.
Python functions are designated as tasks by using a celery-provided decorator (@app.task).

This file is used for starting celery workers on a compute node. Do not change the filename. It must be called "app.py".
Because this app must be running on each worker, and access to nodes is restricted,
please ask the lab member in charge of the cluster to verify the workers have been started.

"""

from celery import Celery

import celeryconfig
from src.celery_task import deep_learning_task as _deep_learning_task

app = Celery('dlsrl')
app.config_from_object(celeryconfig)


@app.task
def deep_learning_task(**kwargs):
    return _deep_learning_task(**kwargs)