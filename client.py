"""
This file is used to submit tasks to one or more nodes.
It uses an sftp client library to upload run.py, and all file sin the user directory.
The idea is to upload to each node a separate configs.csv which specifies all the hyper-parameters of a neural network, for example.
"""
from pathlib import Path
import pysftp
from src import config
from src.starter import Starter
from src.logger import Logger
from src import RUN_FNAME, PROJECT_NAME, USERNAME
from user.options import check_configs_dict, default_configs_dict

# WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'lecun', 'bengio']  # TODO
WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio']
REPS = 4

logger = Logger(default_configs_dict)
starter = Starter(REPS, default_configs_dict, check_configs_dict, logger)

# load hostname aliases from .ssh/config
hostname2ip = {}
h = None
p = Path.home() / '.ssh' / 'config'
with p.open('r') as f:
    for line in f.readlines():
        words = line.split()
        if 'Host' in words:
            h = line.split()[1]
            hostname2ip[h] = None
        elif 'HostName' in words:
            ip = line.split()[1]
            hostname2ip[h] = ip

private_key_pass = (Path.home() / '.rsapub_passwd').read_text().strip('\n')
for worker_name, configs_dict in zip(WORKER_NAMES, starter.gen_configs_dicts()):
    print('Connecting to {}'.format(worker_name))
    sftp = pysftp.Connection(username='ludwig',
                             host=hostname2ip[worker_name],
                             private_key='/home/{}/.ssh/id_rsa'.format(USERNAME),
                             private_key_pass=private_key_pass)
    for p in [config.Dirs.user, config.Dirs.src]:
        for file in p.glob('*.py'):  # exclude __pycache__
            directory = file.parent.stem
            localpath = '{}/{}'.format(directory, file.name)
            remotepath = '{}/{}/{}'.format(PROJECT_NAME, directory, file.name)
            print('Uploading {} to {}'.format(localpath, remotepath))
            try:
                sftp.put(localpath=localpath, remotepath=remotepath)
            except FileNotFoundError:  # directory doesn't exist
                print('WARNING: Directory {} does not exist. It will be created'.format(directory))
                sftp.mkdir('{}/{}'.format(PROJECT_NAME, directory))
                sftp.put(localpath=localpath, remotepath=remotepath)
    sftp.put(localpath=RUN_FNAME,
             remotepath='{}/{}'.format(PROJECT_NAME, RUN_FNAME))
    print('Uploaded {}.\n'.format(RUN_FNAME))



