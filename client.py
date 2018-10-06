"""
This file is used to submit tasks.
It uses an sftp client library to upload run.py, config.csv and any other files needed for task execution.
The idea is to upload to each node a separate config.csv which specifies all the hyperparameters of a neurla network, for example.
"""
from src.starter import Starter

WORKER_NAMES = ['bengio']

starter = Starter()
for wn, config in zip(WORKER_NAMES, starter.gen_configs()):

    # TODO
    # use sftpy to upload run.py and config.csv