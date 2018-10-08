"""
This file is used to submit tasks to one or more nodes.
It uses an sftp client library to upload run.py, and all file sin the user directory.
The idea is to upload to each node a separate configs.csv which specifies all the hyper-parameters of a neural network, for example.
"""
from pathlib import Path
import pysftp
import platform
import psutil
import datetime
from src import config
from src.starter import Starter
from src.logger import Logger
from src import RUN_FNAME, PROJECT_NAME, USERNAME
from user.options import check_configs_dict, default_configs_dict

DISK_USAGE_MAX = 90
# WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'lecun', 'bengio']  # TODO
WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio']
REPS = 4

def make_hostname2ip():
    """load hostname aliases from .ssh/config"""
    res = {}
    h = None
    p = Path.home() / '.ssh' / 'config'
    with p.open('r') as f:
        for line in f.readlines():
            words = line.split()
            if 'Host' in words:
                h = line.split()[1]
                res[h] = None
            elif 'HostName' in words:
                ip = line.split()[1]
                res[h] = ip
    return res


def check_disk_space_used_percent():
    if platform.system() == 'Linux':
        usage_stats = psutil.disk_usage(str(config.Dirs.runs))
        percent_used = usage_stats[3]
        print('Percent Disk Space used: {}'.format(percent_used))
        if percent_used > DISK_USAGE_MAX:
            print('rnnlab: Disk space usage > {}.'.format(DISK_USAGE_MAX), 'red')
            raise Exception
    else:
        print('rnnlab WARNING: Cannot determine disk space on non-Linux platform.')


def make_model_name(hostname):
    time_of_init = datetime.datetime.now().strftime('%m-%d-%H-%M')
    model_name = '{}_{}'.format(hostname, time_of_init)
    path = config.Dirs.runs / model_name
    if path.is_dir():
        raise IsADirectoryError('Directory "{}" already exists.'.format(model_name))
    return model_name


if __name__ == '__main__':
    check_disk_space_used_percent()
    # logging
    logger = Logger(default_configs_dict)
    if not logger.log_path.is_file():
        logger.write_log()
    try:
        logger.delete_incomplete_models()
    except FileNotFoundError:
        print('Could not delete incomplete models. Check log for inconsistencies.')
    hostname2ip = make_hostname2ip()
    # iterate over configs_dicts
    private_key_pass = (Path.home() / '.rsapub_passwd').read_text().strip('\n')
    starter = Starter(REPS, default_configs_dict, check_configs_dict, logger)
    for worker_name, configs_dict in zip(WORKER_NAMES, starter.gen_configs_dicts()):
        configs_dict['model_name'] = make_model_name(worker_name)

        # TODO upload configs_dict

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

