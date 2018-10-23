# LudwigCluster

## Info

The UIUC Learning & language Lab provides compute resources for lab members and collaborators wishing to train large neural network models. 
The resource consists of a file server and 8 compute nodes with GPU acceleration for deep learning tasks.

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

### Linux
It is recommend to use a machine with a Linux OS to submit tasks. 

### Python
Tasks submitted to LudwigCluster must be programmed in Python.

### Access to the shared drive
See the administrator to provide access to the lab's shared drive. Mount the drive at ```/media/lab```.
The share is hosted by the lab's file server using ```samba```, and is shared with each node. 
Because we do not allow direct shell access to nodes, all data and logs must be saved to the shared drive.

### Access to jailed SFTP on one or multiple nodes
You must ask the administrator to provide you with sftp access to one or multiple nodes.
It is recommended to use password-less access via keypair authentication. 
Create ```config``` in ```/home/.ssh```.
Ask the administrator to populate this file with the names of the worker names and their IP addresses.

## Submitting a Task

### 1) LudwigCluster client
Submit neural network jobs to ```LudwigCluster ``` directly from your project by importing the ```LudwigCluster``` client.
First, install the client in your project's virtual environment,

```bash
(venv) pip3 install git+https://github.com/phueb/LudwigCluster.git
```

and import the client:

```python
from ludwigcluster import client, params
```

### 2) 
Create a ```run.py``` file which calls a neural-network training function. 
It should read ```params.csv``` and train a neural network for each row of parameters in ```params.csv```

TODO: should this file be provided by ludwigcluster?

### Logging
By default, the stdout of a submitted job will be redirected to a file located on the shared drive.
After uploading your code, verify that your task is being processed by reading the log file.
If you don't recognize the output in the file, it is likely that the node is currently processing another user's task.
Retry when the node is no longer busy. 

## Note

Tasks cannot be stopped, once started. Please see a administrator to stop running tasks.

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is unaware of every other. Although, each has access to the same shared drive. 