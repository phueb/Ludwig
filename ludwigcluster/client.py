"""
The client is used to submit jobs to one or more nodes in LudwigCluster.
It uses an sftp client library to upload all files in a user's project to LudwigCluster.
"""
from pathlib import Path
import pysftp
import platform
import psutil
import datetime
import pandas as pd
import numpy as np

from ludwigcluster import config
from ludwigcluster.logger import Logger

DISK_USAGE_MAX = 90


# TODO rename all configs_dict occurrences to params

class Client:
    def __init__(self, project_name):
        self.project_name = project_name
        self.hostname2ip = self.make_hostname2ip()
        self.logger = Logger(project_name)
        self.num_workers = len(config.SFTP.worker_names)
        self.private_key_pass = config.SFTP.private_key_pass_path.read_text().strip('\n')
        self.private_key = '{}/.ssh/id_rsa'.format(Path.home())
        self.ludwig = 'ludwig'

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
    def check_lab_disk_space():
        if platform.system() == 'Linux':
            usage_stats = psutil.disk_usage(str(config.Dirs.lab))
            percent_used = usage_stats[3]
            print('Percent Disk Space used at {}: {}'.format(config.Dirs.lab, percent_used))
            if percent_used > DISK_USAGE_MAX:
                print('Disk space usage > {}.'.format(DISK_USAGE_MAX), 'red')
                raise Exception
        else:
            print('WARNING: Cannot determine disk space on non-Linux platform.')

    def make_model_base_name(self, worker_name):
        time_of_init = datetime.datetime.now().strftime(config.Time.format)
        model_name = '{}_{}'.format(worker_name, time_of_init)
        path = config.Dirs.lab / self.project_name / model_name
        if path.is_dir():
            raise IsADirectoryError('Directory "{}" already exists.'.format(model_name))
        return model_name

    def add_reps_to_params_df(self, params_df, reps):
        series_list = []
        for n, params_df_row in params_df.iterrows():
            num_times_logged = self.logger.count_num_times_in_backup(params_df_row)
            num_times_train = reps - num_times_logged
            num_times_train = max(0, num_times_train)
            print('Params {} logged {} times. Will train {} times'.format(
                n, num_times_logged, num_times_train))
            series_list += [params_df_row] * num_times_train
        if not series_list:
            raise RuntimeError('{} replications of each model already exist.'.format(reps))
        else:
            res = pd.concat(series_list, axis=1).T
            return res

    def submit(self, project_path, params_df, reps=1, pattern='*.py', test=True):
        self.check_lab_disk_space()
        self.logger.delete_incomplete_models()
        params_df = self.add_reps_to_params_df(params_df, reps)
        # split params into 8 chunks (one per node)
        worker_names = iter(np.random.permutation(config.SFTP.worker_names))
        for params_df_chunk in np.array_split(params_df, self.num_workers):
            worker_name = next(worker_names)  # distribute jobs across workers randomly
            # params_df_chunk
            num_models = len(params_df_chunk)
            if num_models == 0:
                print('Not submitting to {}'.format(worker_name))
                continue
            base_name = self.make_model_base_name(worker_name)
            params_df_chunk['model_name'] = ['{}_{}'.format(base_name, n) for n in range(num_models)]
            params_df_chunk['runs_dir'] = config.Dirs.lab / self.project_name / 'runs'
            params_df_chunk['backup_dir'] = config.Dirs.lab / self.project_name / 'backup'
            for params_df_row in np.split(params_df_chunk, num_models):
                self.logger.save_params_df_row(params_df_row)
            if test:
                print('TEST: Would submit to {}:'.format(worker_name))
                print(params_df_chunk.T)
                print()
                continue
            # upload
            print('Connecting to {}'.format(worker_name))
            sftp = pysftp.Connection(username='ludwig',
                                     host=self.hostname2ip[worker_name],
                                     private_key=self.private_key,
                                     private_key_pass=self.private_key_pass)
            # upload params.csv
            params_df_chunk.to_csv('params_chunk.csv', index=False)
            sftp.put(localpath='params_chunk.csv',
                     remotepath='{}/{}'.format(self.ludwig, 'params.csv'))
            # upload run.py
            sftp.put(localpath='run.py',
                     remotepath='{}/{}'.format(self.ludwig, 'run.py'))
            # upload all files in project directory
            for file in Path(project_path).glob(pattern):  # use "*.py" to exclude __pycache__
                directory = file.parent.stem
                localpath = '{}/{}'.format(directory, file.name)
                remotepath = '{}/{}/{}'.format(self.ludwig, directory, file.name)
                print('Uploading {} to {}'.format(localpath, remotepath))
                if test:
                    continue  # TODO test
                try:
                    sftp.put(localpath=localpath, remotepath=remotepath)
                except FileNotFoundError:  # directory doesn't exist
                    print('WARNING: Directory {} does not exist. It will be created'.format(directory))
                    sftp.mkdir('{}/{}'.format(self.ludwig, directory))
                    sftp.put(localpath=localpath, remotepath=remotepath)
