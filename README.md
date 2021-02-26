<div align="center">
 <img src="images/logo.png" width="200"> 
</div>


## About

The UIUC Learning & language Lab provides compute resources for lab members and collaborators wishing to train large neural network models. 
The resource consists of a file server and 8 Ubuntu 16.04 machines with GPU acceleration for deep learning tasks.

## Worker Specs

| hostname  |GPU                    |CPU                          |Product Name        |Storage             |
|-----------|-----------------------|-----------------------------|--------------------|--------------------|
| hoff      |1 Geforce GTX 1080     |Intel i7-7700  CPU @ 3.60GHz |Alienware Aurora R6 |256GB SSD + 1TB HDD |
| norman    |1 Geforce GTX 1080     |Intel i7-7700  CPU @ 3.60GHz |Alienware Aurora R6 |256GB SSD + 1TB HDD |
| hebb      |1 Geforce GTX 1080     |Intel i7-7700  CPU @ 3.60GHz |Alienware Aurora R6 |256GB SSD + 1TB HDD |
| hinton    |1 Geforce GTX 1080     |Intel i7-7700  CPU @ 3.60GHz |Alienware Aurora R6 |256GB SSD + 1TB HDD |
| pitts     |1 Geforce GTX 1080     |Intel i7-7700  CPU @ 3.60GHz |Alienware Aurora R6 |256GB SSD + 1TB HDD |
| hawkins   |1 Geforce GTX 1080 Ti  |Intel i7-8700K CPU @ 3.70GHz |Alienware Aurora R7 |256GB SSD + 1TB HDD |
| lecun     |1 Geforce GTX 1080 Ti  |Intel i7-8700K CPU @ 3.70GHz |Alienware Aurora R7 |256GB SSD + 1TB HDD |
| bengio    |1 Geforce GTX 1080 Ti  |Intel i7-8700K CPU @ 3.70GHz |Alienware Aurora R7 |256GB SSD + 1TB HDD |

Installations:
* Ubuntu 16.04.7 LTS
* python3.7.9
* nvidia-430
* pytorch==1.6.0
* transformers==3.0.2


## Requirements & Installation

### Linux or MacOS
Windows is currently not supported due to incompatibility with file names used by Ludwig.

### Python
Tasks submitted to Ludwig must be programmed in Python 3 (the Python3.7 interpreter is used on each worker).

### Access to the shared drive
See the administrator to provide access to the lab's shared drive. Mount the drive at ```/media/ludwig_data```.
The share is hosted by the lab's file server using ```samba```, and is shared with each node. 
Because we do not allow direct shell access to nodes, all data and logs must be saved to the shared drive.

### Installation

In a terminal, type:

```bash
pip3 install git+https://github.com/phueb/Ludwig.git
```

### Project Organization

```ludwig``` requires all Python code be located in a folder inside the root directory of your project. 
Additionally, inside this folder, create two Python files:
* ```params.py```: contains information about which parameters to use for each job
* ```config.py```: contains basic information like the name of the user's project

See the `Example` folder for an example of what to put into these files.

## Submitting a Job

Once you have installed `ludwig` and set up your project appropriately, use the command-line tool to submit your job.
To submit jobs, go to your project root folder, and invoke the command-line tool that has been installed:

```bash
ludwig
``` 

You may get an error message saying that hostkeys cannot be found.
To add the worker's hostkeys to your machine, use `sftp` to connect to each worker, 
to trigger a prompt asking to copy the worker's hostkey. 
For example,

```bash
sftp ludwig@hebb
```

When asked to save the hostkey, enter `yes` and hit `Enter`.

Alternatively, skip hostkey checking with the `-s` flag:

```bash
ludwig -s
```

### Viewing output of jobs

By default, the stdout of a submitted job will be redirected to a file located on the shared drive.
After uploading your code, verify that your task is being processed by reading the log file.
If you don't recognize the output in the file, it is likely that the node is currently processing another user's task.
Retry when the node is no longer busy. 

To check the status of a Ludwig worker (e.g. hebb):

```bash
ludwig-status -w hebb
```

### Re-submitting

Any time new jobs are submitted, any previously submitted jobs associated with the same project and still running, 
will be killed.

## Advanced 

### Non-standard mount location

Across different operating systems, the default mount location is different.
That means that the path to the shared drive will be different.
To upload data or third-party source code to the shared drive, ```ludwig``` must be explicitly told where to find the shared drive:

For example, if `ludwig_data` is mounted at `/Volumes/ludwig_data`:

```
ludwig -mnt /Volumes/ludwig_data
```
The ```-mnt``` flag is used to specify where the shared drive is mounted on the user's machine.

### Reading from File Server during remote job execution

A user might want to load a dataset from the shared drive.
To do so, the path to the shared drive from the Ludwig worker must be known.
The path is auto-magically added by `Ludwig` and can be accessed via `param2val['project_path`].
For example, loading a corpus from the shared drive might look like the following:

```python
def main(param2val):
    
    from pathlib import Path
    
    project_path = Path(param2val['project_path'])
    corpus_path = project_path / 'data' / f'{param2val["corpus_name"]}.txt'
    train_docs, test_docs = load_corpus(corpus_path)
```

### Saving Job Results
Job results, such as learning curves, or other 1-dimensional performance measures related to neural networks for example,
 should be returned by job.main() as a list of pandas DataFrame objects.
These will be automatically saved to the shared drive after a job has completed.

Alternatively, if the data is too big to be held in memory, it is recommended to write the data to disk,
and manually move it to the shared drive at the end of main.job(), as illustrated here: 

```python
from pathlib import Path

def main(param2val):

    # some neural network training code
    # ....
    
    # get save_path - all files in this location will be moved to file-server
    save_path = Path(param2val['save_path'])
    
    # make sure to create the directory if running job on local machine (Ludwig creates this directory automatically on worker, however)
    if not save_path.exists():
        save_path.mkdir(parents=True)
    
    # save a file
    with (save_path / 'test.txt').open('r') as f:
        f.write('test') 
    
```

## Development & Debugging

Sometimes you may wish to use your local machine instead of a Ludwig worker to execute your job.
To do so, navigate to the root directory of your project and use the `--local` flag as shown below.

```bash
ludwig --local
```

Results will still be saved to the server. 
To run jobs without access to the server, use the `--isolated` flag, as shown below. 
This is useful for developing and debugging your code without having to submit it to a Ludwig worker for execution.

```bash
ludwig --isolated
```
## Documentation

More information about how the system was setup can be found at [https://docs.philhuebner.com/ludwig](https://docs.philhuebner.com/ludwig).
