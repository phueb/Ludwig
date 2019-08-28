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
See the administrator to provide access to the lab's shared drive. Mount the drive at ```/media/research_data```.
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

Here is an example file:

```python
from pathlib import Path
from ludwigcluster.client import Client

# create list of neural network parameter configurations to trian on cluster
param2val_list = [param2val1, param2val2] # each is a dict mapping a parameter name to a value
# submit
client = Client('your_project_name')  # creates a directory on server 
client.submit(src_ps=[Path('src')],  # specify path to source code (is uploaded to worker)
              data_ps=[Path('corpora'), Path('tasks')],  # specify paths to any data (is uploaded to file server)
              param2val_list=param2val_list,
              reps=2)  # number of replications per job
```

### 2) 
Create a ```run.py``` file which calls a neural-network training function. 
Here is an example of the content of ```run.py```:

```python
from pathlib import Path
import pickle
from your_module import neural_net_job

hostname = 'your_hostname'
# load list of neural network configurations provided by ludwigcluster (saved to file server)
p = Path('/media/research_data/<your_project_name>') / '{}_param2val_chunk.pkl'.format(hostname)  
with p.open('rb') as f:
    param2val_chunk = pickle.load(f)
# iterate over neural network configurations, and for each, do some neural_net_job
for param2val in param2val_chunk:
    neural_net_job(param2val)
```

### Saving Data
Any data (e.g. accuracy per epoch) that needs to persist, should be written to the worker. 
Write any data to a directory (with a name unique to your project) on the worker.
It is recommended you move all files to the file-server only after a neural network has completed training.
This prevents accumulation on the file-server of data from jobs that have not completed. 
For example:

```python
from pathlib import Path
import shutil

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

Tasks cannot be stopped, once started. Please see a administrator to stop running tasks.

Strictly speaking, LudwigCluster is not really a "cluster". 
Each node is unaware of every other. Although, each has access to the same shared drive. 