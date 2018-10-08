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
Tasks submitted to LudwigCluster must be programmed in python.

### Access to the shared drive
See the administrator to provide access to the lab's shared drive. Mount the drive at ```/media/lab```.
The share is hosted by the lab's file server using ```samba```, and is shared with each node. 
Because we do not allow direct shell access to nodes, all data and logs must be saved to the shared drive.

### Access to jailed SFTP on one or multiple nodes
You must ask the administrator to provide you with sftp access to one or multiple nodes.
It is recommended to use password-less access via keypair authentication. 
To submit a task to LudwigCluster, transfer your source code to a node. 
Make sure to include a file ```run.py```. 
A file-watcher is constantly watching for changes to ```run.py``` and whenever a new version is uploaded, ```run.py``` will automatically be executed in a subprocess.

### ssh config
Create ```config``` in ```/home/.ssh```.
Ask the administrator to populate this file with the names of the worker names and their IP addresses.
### Project directory
Each task must be associated with a project. 
Ask the administrator to create a directory ```<PROJECTNAME>``` in ```/var/sftp``` on one or more nodes. 
Because ```/var/sftp``` is owned by ```root```, the administrator must give the user ```ludwig``` ownership of the directory:
```bash
chmod ludwig:ludwig <PROJECTNAME>
``` 
The administrator must also start the file-watcher:
```bash
cd /var/sftp/<PROJECTNAME>
sudo python3 watcher.py
```
## Submitting a Task

### 1) sftp
Let's take for example a user who would like to submit a task to ```bengio```. 
First, connect to ```bengio```'s sftp server:
```bash
sftp ludwig@bengio
```

Next, upload all files needed for the task (or only those with revisions, if previously uploaded).
Make sure to upload ```run.py``` - even if no revisions have been made to it.
```bash
sftp> put src/*.py <PROJECTNAME>/src/
sftp> put run.py <PROJECTNAME>/
```

### 2) client.py
Alternatively, use ```client.py``` to automate this task across multiple nodes. 

### 3) pip install LudwigCluster (recommended)
Make ```LudwigCluster available ``` in your project, by installing this repository in your project's virtualenv:
```(venv) pip install git+https://github.com/languagelearninglab/LudwigCluster.git```

TODO - what's next?

### Logging
By default, the stdout of ```run.py``` will be redirected to a text file located on the shared drive.
After uploading your code, verify that your task is being processed by reading the log file.
If you don't recognize the output in the logfile, it is likely that the node is currently processing another user's task.
Retry when the node is no longer busy. 

## Note

Tasks cannot be stopped, once started. Please see a administrator to stop running tasks.

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is unaware of every other. Although, each has access to the same shared drive. 