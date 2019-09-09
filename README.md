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

### Project Organization

```ludwigcluster``` requires that the user create two special modules:
* ```src.params```: contains information about which parameters to use for each job
* ```src.config```: contains basic information like the name of the user's project

### Access to the shared drive
See the administrator to provide access to the lab's shared drive. Mount the drive at ```/media/research_data```.
The share is hosted by the lab's file server using ```samba```, and is shared with each node. 
Because we do not allow direct shell access to nodes, all data and logs must be saved to the shared drive.

### Access to jailed SFTP on one or multiple nodes
You must ask the administrator to provide you with sftp access to one or multiple nodes.
It is recommended to use password-less access via keypair authentication. 
Create ```config``` in ```/home/.ssh```.
Ask the administrator to populate this file with the names of the worker names and their IP addresses.

## Submitting a Job

### 1) Install ludwigcluster

In a terminal, type:

```bash
(venv) pip3 install git+https://github.com/phueb/LudwigCluster.git
```

### 2) run.py

Copy the ```run.py``` file provided by ```ludwigcluster``` into the root folder of your project.

### 3) The command-line tool

To submit jobs, go to your project root folder, and invoke the command-line tool that has been installed:

```bash
(venv) ludwig
``` 

### Saving Data
Any data (e.g. accuracy per epoch) that needs to persist, should be returned by job.main() as a list of pandas DataFrame objects.
These will be automatically saved to the shared drive after a job has completed.

Alternatively, if the data is too big to be held in memory, it is recommended to write the data to disk,
and manually move it to the shared drive at the end of main.job(), as illustrated here: 

```python
from pathlib import Path
import shutil

def main():

    for epoch in range(10):
        data = train_epoch()
        save_to_worker(data)  # save intermediate data to worker
    
    # at end of training copy all data files to file server
    for data_path in Path('/var/sftp/ludwig/<unique_data_folder_name>').glob('data*.csv'):
        src = str(data_path)
        dst = '/media/research_data/<your_project_name>/{}'.format(data_path.name)
        shutil.move(src, dst)
```

### Logging
By default, the stdout of a submitted job will be redirected to a file located on the shared drive.
After uploading your code, verify that your task is being processed by reading the log file.
If you don't recognize the output in the file, it is likely that the node is currently processing another user's task.
Retry when the node is no longer busy. 

## Note

Calling ```ludwig``` while previously submitted jobs are still being executed, 
will stop all previously submitted jobs.

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is unaware of every other. Although, each has access to the same shared drive. 