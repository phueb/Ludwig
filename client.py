"""
This file is used to submit tasks to one or more nodes.
It uses an sftp client library to upload run.py, and all file sin the user directory.
The idea is to upload to each node a separate configs.csv which specifies all the hyper-parameters of a neural network, for example.
"""
import csv
from pathlib import Path
import pysftp
import platform
import psutil
import datetime
from ludwigcluster import config
from ludwigcluster.starter import Starter
from ludwigcluster.logger import Logger

DISK_USAGE_MAX = 90
# WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'lecun', 'bengio']  # TODO
WORKER_NAMES = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio']
REPS = 4


class Client:
    def __init__(self, project_name, default_configs_dict, check_fn):
        self.project_name = project_name
        self.default_configs_dict = default_configs_dict
        self.hostname2ip = self.make_hostname2ip()
        self.logger = Logger(project_name, default_configs_dict)
        self.starter = Starter(REPS, default_configs_dict, check_fn, self.logger.load_log())

    @staticmethod
    def make_hostname2ip():
        """load hostname aliases from .ssh/config"""
        res = {}
        h = None
        p = Path.home() / '.ssh' / 'config'
        if not p.exists():
            raise FileNotFoundError('Please specify hostname-to-IP mappings in .ssh/config.')
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

    @staticmethod
    def check_disk_space_used_percent():
        if platform.system() == 'Linux':
            usage_stats = psutil.disk_usage(str(config.Dirs.lab))
            percent_used = usage_stats[3]
            print('Percent Disk Space used: {}'.format(percent_used))
            if percent_used > DISK_USAGE_MAX:
                print('Disk space usage > {}.'.format(DISK_USAGE_MAX), 'red')
                raise Exception
        else:
            print('WARNING: Cannot determine disk space on non-Linux platform.')

    def make_model_name(self, hostname):
        time_of_init = datetime.datetime.now().strftime('%m-%d-%H-%M')
        model_name = '{}_{}'.format(hostname, time_of_init)
        path = config.Dirs.lab / self.project_name / model_name
        if path.is_dir():
            raise IsADirectoryError('Directory "{}" already exists.'.format(model_name))
        return model_name

    def make_new_configs_dicts(self):
        p = config.Dirs.lab / self.project_name / 'configs.csv'
        if not p.exists():
            print('Did not find configs.csv in {}'.format(p))
        res = list(csv.DictReader(p.open('r')))
        print('New configs:')
        for config_id, d in enumerate(res):
            print('Config {}:'.format(config_id))
            for k, v in sorted(d.items()):
                print('{:>20} -> {:<20}'.format(k, v))
        return res

    def submit(self, project_path, pattern='*.py'):
        self.check_disk_space_used_percent()
        # delete old
        try:
            self.logger.delete_incomplete_models()
        except FileNotFoundError:
            print('Could not delete incomplete models. Check log for inconsistencies.')
        new_configs_dicts = self.make_new_configs_dicts()
        # iterate over configs_dicts
        private_key_pass = config.SFTP.private_key_pass_path.read_text().strip('\n')
        for worker_name, configs_dict in zip(WORKER_NAMES,
                                             self.starter.gen_configs_dicts(new_configs_dicts)):
            configs_dict['model_name'] = self.make_model_name(worker_name)

            # TODO upload configs_dict

            print('Connecting to {}'.format(worker_name))
            sftp = pysftp.Connection(username='ludwig',
                                     host=self.hostname2ip[worker_name],
                                     private_key='{}/.ssh/id_rsa'.format(Path.home()),
                                     private_key_pass=private_key_pass)
            # upload
            found_watched_fname = False
            for file in Path(project_path).glob(pattern):  # use "*.py" to exclude __pycache__
                if file.name == config.SFTP.watched_fname:
                    found_watched_fname = True
                directory = file.parent.stem
                localpath = '{}/{}'.format(directory, file.name)
                remotepath = '{}/{}/{}'.format(self.project_name, directory, file.name)
                print('Uploading {} to {}'.format(localpath, remotepath))
                try:
                    sftp.put(localpath=localpath, remotepath=remotepath)
                except FileNotFoundError:  # directory doesn't exist
                    print('WARNING: Directory {} does not exist. It will be created'.format(directory))
                    sftp.mkdir('{}/{}'.format(self.project_name, directory))
                    sftp.put(localpath=localpath, remotepath=remotepath)
            # make sure to include run.py
            if not found_watched_fname:
                raise RuntimeError('Did not find {} in project_path.'.format(config.SFTP.watched_fname))