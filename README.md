# LudwigCluster

## Info

This cluster consists of a file server and 8 compute nodes with GPU acceleration for deep learning tasks.
Access to compute resources are provided by the UIUC Learning & language Lab in the form of credentials to a distributed task queue hosted on the file server.

Compute Node hostnames:
* hoff
* norman
* hebb
* hinton
* pitts
* hawkins
* lecun
* bengio

## Specs

Each node is an Alienware Aurora with the following specs:
* 1 NVIDIA GTX 1080 GPU
* CUDA 8.0
* cudnn 6
* python3.5
* tensorflow-gpu
* pytorch


## Requirements

### Python
At the moment, only tasks implemented as python functions can be submitted to LudwigCluster.

### Access to file-server
Tasks submitted to LudwigCluster requires ssh access to the file-server. 
You may develop your code locally, and copy the source code files to the file-server.
To do so, create a project directory on the file-server ```/home/lab/cluster/celery/<APPNAME>)```.
```/home/lab/)``` is a shared drive, and therefore accessible to each node.

### Celery config file
Have a lab member place a configuration file (containing access credentials to the distributed task queue) ```celeryconfig.py``` in the root directory of your project. 
This lets the worker processes know how to access the distributed task queue.

### Worker Processes
Before submitting tasks, each node must have celery worker process running in the background.
Because access to each node is restricted, please ask a lab member to verify workers are online.

For reference, to start a worker process (requires remote access to nodes):
```bash
cd /media/lab/cluster/celery/${APPNAME}
nohup celery worker -l info -A app --concurrency 1 > /media/lab/cluster/logs/${APPNAME}/$(hostname)_log.txt 2>&1 &
```

And to stop a worker process:
```bash
ps auxww | grep "celery worker" | awk '{print $2}' | xargs kill -9
```

## Logging
Create a directory  ```/home/lab/cluster/logs/<APPNAME>```. Here you will be able to view the stdout of your task.

## Note

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is nothing more than a worker consuming tasks form a distributed task queue.