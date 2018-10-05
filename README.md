# LudwigCluster

## Info

This cluster consists of a file server and 8 compute nodes with GPU acceleration for deep learning tasks.
Access to compute resources are provided by the UIUC Learning & language Lab in the form of credentials to a distributed task queue hosted on the file server.

## Specs

| hostname  |GPU                    | Model               |
|-----------|-----------------------|---------------------|
| hoff      |1 Geforce GTX 1080     | Alienware Aurora R6 |
| norman    |1 Geforce GTX 1080     | Alienware Aurora R6 |
| hebb      |1 Geforce GTX 1080     | Alienware Aurora R6 |
| hinton    |1 Geforce GTX 1080     | Alienware Aurora R6 |
| pitts     |1 Geforce GTX 1080     | Alienware Aurora R6 |
| hawkins   |1 Geforce GTX 1080 Ti  | Alienware Aurora R7 |
| lecun     |1 Geforce GTX 1080 Ti  | Alienware Aurora R7 |
| bengio    |1 Geforce GTX 1080 Ti  | Alienware Aurora R7 |

All machines are configured to use:
* CUDA 8.0
* cudnn 6
* python3.5
* tensorflow-gpu
* pytorch


## Requirements

### Python
At the moment, only tasks implemented as python functions can be submitted to LudwigCluster.

### Access to shared drive (hosted by the file-server)
See a lab member to provide access to the lab's shared drive. Mount the drive at ```/media/lab```.
You may develop your code locally, and when ready to submit a task, copy the source code files to the shared drive at ```/media/lab/cluster/celery/<APPNAME>```.
Developing on the shared drive is possible, but not recommended. 
Doing so strains the file-server's resources and slows development due to working over a network connection. 
Note that ```/home/lab/``` is shared with each node.

### Celery config file
Have a lab member place a configuration file (containing access credentials to the distributed task queue) ```celeryconfig.py``` in the root directory of your project. 
This lets the worker processes know how to access the distributed task queue.

### Worker Processes
Before submitting tasks, each node must have celery worker process running in the background.
Because access to each node is restricted, please ask a lab member to verify workers are online.

For reference, to start all worker processes (requires remote access to nodes):
```bash
cd /media/lab/cluster/celery/${APPNAME}
nohup celery worker -l info -A app --concurrency 1 > /media/lab/cluster/logs/${APPNAME}/$(hostname)_log.txt 2>&1 &
```

Because worker processes can only compute tasks in the state they were at the time of startup, 
it is recommended to configure automatic restarting of all worker processes whenever a change to the python code has been made.
The lab member in charge of LudwigCluster will use ```watchdog``` to start a worker process with auto-restarting:
```bash
watchmedo auto-restart -d src/ -p '*.py' -- celery worker -l info -A foo
```

In case a worker process needs to be shut down:
```bash
ps auxww | grep "celery worker" | awk '{print $2}' | xargs kill -9
```

## Logging
Create  ```/media/lab/cluster/logs/<APPNAME>```. 
The stdout of worker processes will be redirected to text files in this directory.


## Note

A lab member with access to the file-server might want to view stats about the task queue. 
To do so, login to the file-server, and write:
```bash
cd /home/lab/cluster/celery/${APPNAME}
nohup flower -A app --port=5001 > /dev/null 2>&1 &
```
Then visit ```http://<FILE-SERVER-IP>:5001/``` to view browser interface. 
A user without file-server access may access the same interface if the ```flower``` server has previously been started.

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is nothing more than a worker consuming tasks form a distributed task queue.