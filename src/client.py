"""
The client is used to submit jobs to one or more machines in Ludwig.
It uses an sftp client library to upload all files in a user's project to Ludwig.
"""
from itertools import cycle
from pathlib import Path
import pysftp
import platform
import psutil
import datetime
import pickle
import numpy as np
import yaml
from distutils.dir_util import copy_tree
import sys
import time

from src import config
from src.logger import Logger
from src import run

DISK_USAGE_MAX = 90


class Client:
    def __init__(self, project_name, param2default):
        self.project_name = project_name
        self.param2default = param2default
        self.hostname2ip = self.make_hostname2ip()
        self.logger = Logger(project_name)
        self.num_workers = len(config.SFTP.worker_names)
        self.private_key_pass = config.SFTP.private_key_pass_path.read_text().strip('\n')
        self.private_key = '{}/.ssh/id_rsa'.format(Path.home())

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
            usage_stats = psutil.disk_usage(str(config.Dirs.research_data))
            percent_used = usage_stats[3]
            print('Percent Disk Space used at {}: {}'.format(config.Dirs.research_data, percent_used))
            if percent_used > DISK_USAGE_MAX:
                raise RuntimeError('Disk space usage > {}.'.format(DISK_USAGE_MAX))
        else:
            print('WARNING: Cannot determine disk space on non-Linux platform.')

    def make_job_base_name(self, worker_name):
        time_of_init = datetime.datetime.now().strftime(config.Time.format)
        res = '{}_{}'.format(worker_name, time_of_init)
        path = config.Dirs.research_data / self.project_name / res
        if path.is_dir():
            raise IsADirectoryError('Directory "{}" already exists.'.format(res))
        return res

    def add_reps(self, param2val_list, reps):
        res = []
        for n, param2val in enumerate(param2val_list):
            param_name = param2val['param_name']
            num_times_logged = self.logger.count_num_times_logged(param_name)
            num_times_run = reps - num_times_logged
            num_times_run = max(0, num_times_run)
            print('{:<10} logged {:>3} times. Will execute job {:>3} times'.format(
                param_name, num_times_logged, num_times_run))
            res += [param2val.copy() for _ in range(num_times_run)]  # make sure that each is unique (copied)
        if not res:
            time.sleep(1)
            raise SystemExit('{} replication{} of each job already exist{}.'.format(reps,
                                                                                    's' if reps > 1 else '',
                                                                                    ' ' if reps > 1 else 's'))
        return res

    @staticmethod
    def _iter_over_cycles(param2opts):
        """
        return list of mappings from param name to integer which is index to possible param values
        all possible combinations are returned
        """
        lengths = []
        for k, v in param2opts:
            lengths.append(len(v))
        total = np.prod(lengths)
        num_lengths = len(lengths)

        # cycles
        cycles = []
        prev_interval = 1
        for n in range(num_lengths):
            l = np.concatenate([[i] * prev_interval for i in range(lengths[n])])
            if n != num_lengths - 1:
                c = cycle(l)
            else:
                c = l
            cycles.append(c)
            prev_interval *= lengths[n]

        # iterate over cycles, in effect retrieving all combinations
        param_ids = []
        for n, i in enumerate(zip(*cycles)):
            param_ids.append(i)
        assert sorted(list(set(param_ids))) == sorted(param_ids)
        assert len(param_ids) == total
        return param_ids

    def list_all_param2vals(self, param2requests, update_d=None, add_names=True):

        # check that requests are lists
        for k, v in param2requests.items():
            assert isinstance(v, list)

        # complete partial request made by user
        full_request = {k: [v] if k not in param2requests else param2requests[k]
                        for k, v in self.param2default.copy().items()}
        #
        param2opts = tuple(full_request.items())
        param_ids = self._iter_over_cycles(param2opts)

        res = []
        for ids in param_ids:
            # map param names to integers corresponding to which param value to use
            param2val = {k: v[i] for (k, v), i in zip(param2opts, ids)}
            if add_names:
                param2val.update({'param_name': None, 'job_name': None})
            if isinstance(update_d, dict):
                param2val.update(update_d)

            res.append(param2val)
        return res

    def submit(self, src_p, param2requests, extra_folder_ps,
               reps=1, test=True, worker=None, mnt_path_name=None):
        self.check_lab_disk_space()

        # check that requests are lists
        for k, v in param2requests.items():
            assert isinstance(v, list)

        # make list of hyper-parameter configurations to submit
        param2val_list = self.list_all_param2vals(param2requests)

        # copy extra folders to file server  (can be Python packages, which will be importable, or contain data)
        if mnt_path_name is None:
            mnt_p = config.Dirs.research_data
        else:
            mnt_p = Path(mnt_path_name)
            assert mnt_p.exists()  # TODO test
        for package_p in extra_folder_ps:
            src = str(package_p)
            dst = str(mnt_p / self.project_name / package_p.name)
            print('Copying {} to {}'.format(src, dst))
            copy_tree(src, dst)

        # add param_name to param2val
        print('Assigning param_names...')
        for n, param2val in enumerate(param2val_list):
            old_or_new, param_name = self.logger.get_param_name(param2val)
            param2val['param_name'] = param_name
            print('param2val {}/{} assigned to {} "{}"'.format(n + 1, len(param2val_list), old_or_new, param_name))
            sys.stdout.flush()

        # add reps
        param2val_list = self.add_reps(param2val_list, reps)

        # distribute (expensive) jobs approximately evenly across workers
        param2val_list = np.random.permutation(param2val_list)
        sys.stdout.flush()

        # split into chunks (one per node)
        worker_names = iter(np.random.permutation(config.SFTP.worker_names)) if worker is None else iter([worker])
        num_workers = 1 if worker is not None else self.num_workers
        for param2val_chunk in np.array_split(param2val_list, num_workers):
            try:
                worker_name = next(worker_names)  # distribute jobs across workers randomly
            except StopIteration:
                raise SystemExit('Using only worker "{}" because "worker" arg is not None.'.format(worker))
            #
            if len(param2val_chunk) == 0:
                print('Not submitting to {}'.format(worker_name))
                continue

            # add job_name to each param2val
            base_name = self.make_job_base_name(worker_name)
            for n, param2val in enumerate(param2val_chunk):
                job_name = '{}_num{}'.format(base_name, n)
                param2val['job_name'] = job_name

            # save chunk to shared drive (after addition of job_name)
            p = config.Dirs.research_data / self.project_name / '{}_param2val_chunk.pkl'.format(worker_name)
            with p.open('wb') as f:
                pickle.dump(param2val_chunk, f)

            # console
            print('Connecting to {}'.format(worker_name))
            for param2val in param2val_chunk:
                print(param2val)

            # connect via sftp
            sftp = pysftp.Connection(username='ludwig',
                                     host=self.hostname2ip[worker_name],
                                     private_key=self.private_key,
                                     private_key_pass=self.private_key_pass)

            # upload src code to worker
            local_path = str(src_p)
            remote_path = '{}/{}'.format(config.SFTP.watched_dir_name, src_p.name)
            print('Uploading {} to {}'.format(local_path, remote_path))
            sftp.makedirs(remote_path)
            sftp.put_r(localpath=local_path, remotepath=remote_path)
            sys.stdout.flush()

            # upload run.py
            if test:
                print('Test successful. Not uploading run.py.')
            else:
                sftp.put(localpath=run.__file__,
                         remotepath='{}/{}'.format(config.SFTP.watched_dir_name, 'run_{}.py'.format(src_p.name)))

            print('--------------')
            print()

    def gen_param_ps(self, param2requests, runs_p=None, label_params=None):
        """
        Return path objects that point to folders with job results.
         Folders located in those paths are each generated with the same parameter configuration.
         Use this for retrieving data after a job has been completed
        """
        print('Requested:')
        print(param2requests)
        print()

        label_params = sorted(set([param for param, val in param2requests.items()
                                   if val != self.param2default[param]] + (label_params or [])))

        requested_param2vals = self.list_all_param2vals(param2requests, add_names=False)

        if runs_p is None:
            runs_p = config.Dirs.research_data / self.project_name / 'runs'
        for param_p_ in runs_p.glob('param_*'):
            print('Checking {}...'.format(param_p_))

            # load param2val
            with (param_p_ / 'param2val.yaml').open('r') as f:
                param2val = yaml.load(f, Loader=yaml.FullLoader)
            loaded_param2val = param2val.copy()
            del loaded_param2val['param_name']
            del loaded_param2val['job_name']

            # is match?
            if loaded_param2val in requested_param2vals:
                label_ = '\n'.join(['{}={}'.format(param, param2val[param]) for param in label_params])
                label_ += '\nn={}'.format(len(list(param_p_.glob('*num*'))))
                print('Param2val matches')
                print(label_)
                yield param_p_, label_
            else:
                print('Params do not match')


