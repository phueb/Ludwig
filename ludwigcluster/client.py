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

from ludwigcluster import config
from ludwigcluster.logger import Logger

DISK_USAGE_MAX = 90


# TODO rename all configs_dict occurrences to params

class Client:
    def __init__(self, project_name):
        self.project_name = project_name
        self.hostname2ip = self.make_hostname2ip()
        self.logger = Logger(project_name)

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

    def make_model_name(self, worker_name):
        time_of_init = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        model_name = '{}_{}'.format(worker_name, time_of_init)
        path = config.Dirs.lab / self.project_name / model_name
        if path.is_dir():
            raise IsADirectoryError('Directory "{}" already exists.'.format(model_name))
        return model_name

    def chunk_params(self, params_df, reps):


        # TODO this should split new_params_list into 8 random chunks
        raise SystemExit

        for n, params_df_row in params_df.iterrows():
            print('==================================')
            num_times_logged = 0
            num_times_logged += self.count_num_times_logged(params_df_row)
            num_times_train = reps - num_times_logged
            num_times_train = max(0, num_times_train)
            print('Logged {} times'.format(num_times_logged))
            print('Will train {} times'.format(num_times_train))
            print('==================================')
            if num_times_train > 0:
                for _ in range(num_times_train):
                    yield params_df_row

    def count_num_times_logged(self, params_df_row):
        num_times_logged = 0
        for n, log_df_row in self.logger.load_log().iterrows():
            if all([params_df_row[k] == log_df_row[k] for k in params_df_row.index]):
                num_times_logged += 1
        return num_times_logged

    def submit(self, project_path, params_df, reps=1, pattern='*.py', test=True):
        self.check_disk_space_used_percent()
        # delete old
        try:
            self.logger.delete_incomplete_models()
        except FileNotFoundError:
            print('Could not delete incomplete models. Check log for inconsistencies.')
        # chunk new params into 8 (one chunk per node)
        private_key_pass = config.SFTP.private_key_pass_path.read_text().strip('\n')
        for worker_name, params_chunk in zip(config.SFTP.worker_names,
                                             self.chunk_params(params_df, reps)):


            # TODO params_chunk

            raise SystemExit('Stopped')

            # params
            params.model_name = self.make_model_name(worker_name)
            params.runs_dir = config.Dirs.lab / self.project_name / 'runs'
            params.backup_dir = config.Dirs.lab / self.project_name / 'backup'
            if not test:
                self.logger.write_param_file(params)  # TODO this takes a single param file - no longer works
            # upload
            print('Connecting to {}'.format(worker_name))
            sftp = pysftp.Connection(username='ludwig',
                                     host=self.hostname2ip[worker_name],
                                     private_key='{}/.ssh/id_rsa'.format(Path.home()),
                                     private_key_pass=private_key_pass)
            # upload params file (will be deleted after job is completed)
            sftp.put(localpath='{}/{}/{}'.format(
                config.Dirs.lab, self.project_name, params.model_name, 'params.csv'),
                     remotepath='{}/{}'.format(self.project_name, '{}_params.csv'.format(params.model_name)))  # TODO test
            # upload all files in project directory
            found_watched_fname = False
            for file in Path(project_path).glob(pattern):  # use "*.py" to exclude __pycache__
                if file.name == config.SFTP.watched_fname:
                    found_watched_fname = True
                directory = file.parent.stem
                localpath = '{}/{}'.format(directory, file.name)
                remotepath = '{}/{}/{}'.format(self.project_name, directory, file.name)
                print('Uploading {} to {}'.format(localpath, remotepath))
                if test:
                    continue  # TODO test
                try:
                    sftp.put(localpath=localpath, remotepath=remotepath)
                except FileNotFoundError:  # directory doesn't exist
                    print('WARNING: Directory {} does not exist. It will be created'.format(directory))
                    sftp.mkdir('{}/{}'.format(self.project_name, directory))
                    sftp.put(localpath=localpath, remotepath=remotepath)
            if not found_watched_fname:
                raise RuntimeError('Watcher will not be triggered because {} was not uploaded.'.format(
                    config.SFTP.watched_fname))
