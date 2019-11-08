"""
The client is used to submit jobs to one or more compute machines at the UIUC Learning & Language Lab
An sftp-client library is used to upload code files to each machine.
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
import os
from cached_property import cached_property
from typing import List, Dict, Optional, Any, Tuple

from ludwig import config
from ludwig import print_ludwig
from ludwig.logger import Logger
from ludwig import run

DISK_USAGE_MAX = 90


class Client:
    def __init__(self,
                 project_name: str,
                 param2default: Dict[str, Any],
                 unittest: bool = False
                 ):
        self.project_name = project_name
        self.param2default = param2default
        self.unittest = unittest
        #
        self.num_online_workers = len(config.SFTP.online_worker_names)
        self.runs_path = config.WorkerDirs.research_data / self.project_name / 'runs'

    @cached_property
    def logger(self):
        return Logger(self.project_name)

    @staticmethod
    def make_worker2ip():
        """load hostname aliases from .ssh/ludwig_config"""
        res = {}
        h = None
        p = config.SFTP.path_to_ssh_config
        if not p.exists():
            raise FileNotFoundError('Please specify hostname-to-IP mappings in {}'.format(p))
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
    def check_server_disk_space():
        """
        this returns disk space used on server, not locally - verified on Linux
        """
        if platform.system() == 'Linux':
            usage_stats = psutil.disk_usage(str(config.WorkerDirs.research_data))
            percent_used = usage_stats[3]
            print_ludwig('Percent Disk Space used at {}: {}'.format(config.WorkerDirs.research_data, percent_used))
            if percent_used > DISK_USAGE_MAX:
                raise RuntimeError('Disk space usage > {}.'.format(DISK_USAGE_MAX))
        else:
            print_ludwig('WARNING: Cannot determine disk space on non-Linux platform.')

    def make_job_base_name(self,
                           worker_name: str
                           ):
        time_of_init = datetime.datetime.now().strftime(config.Time.format)
        res = '{}_{}'.format(worker_name, time_of_init)
        path = config.WorkerDirs.research_data / self.project_name / res
        if path.is_dir():
            raise IsADirectoryError('Directory "{}" already exists.'.format(res))
        return res

    def add_reps(self, param2val_list, reps):
        res = []
        for n, param2val in enumerate(param2val_list):
            param_name = param2val['param_name']
            num_times_logged = self.logger.count_num_times_logged(param_name) if not self.unittest else 0
            num_times_run = reps - num_times_logged
            num_times_run = max(0, num_times_run)
            print_ludwig('{:<10} logged {:>3} times. Will execute job {:>3} times'.format(
                param_name, num_times_logged, num_times_run))
            res += [param2val.copy() for _ in range(num_times_run)]  # make sure that each is unique (copied)
        if not res:
            time.sleep(1)
            raise SystemExit('{} replication{} of each job already exist{}.'.format(reps,
                                                                                    's' if reps > 1 else '',
                                                                                    ' ' if reps > 1 else 's'))
        return res

    @staticmethod
    def _iter_over_cycles(param2opts: Tuple[Any, ...],
                          ):
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

    def list_all_param2vals(self,
                            param2requests: Dict[str, list],
                            ) -> List[Dict[str, Any]]:

        # check that requests are lists
        for k, v in param2requests.items():
            if not isinstance(v, list):
                raise ValueError('Ludwig: Values in param2requests must be of type list.')

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
            res.append(param2val)
        return res

    def submit(self,
               src_name: str,
               param2requests: Dict[str, list],
               extra_paths: List[Path],
               reps: int = 1,
               no_upload: bool = True,
               worker: Optional[str] = None,
               mnt_path_name: Optional[str] = None,  # path to research_data (the shared drive)
               ) -> None:

        # mount point
        if sys.platform == 'darwin':
            default_mnt_point = '/Volumes'
        elif sys.platform == 'linux':
            default_mnt_point = '/media'
        else:
            # unknown default - user must specify mount point via environment variable
            default_mnt_point = os.environ['LUDWIG_MNT']

        # path to research_data (located on file server)
        if mnt_path_name is None:
            research_data_path = Path(default_mnt_point) / config.WorkerDirs.research_data.name
        else:
            research_data_path = Path(mnt_path_name)

        # ------------------------------- checks start

        assert self.project_name.lower() == src_name  # TODO what about when src name must be different?
        # this must be true because in run.py project_name is converted to src_name

        if not os.path.ismount(str(research_data_path)):
            raise SystemExit(f'Failed to mount {research_data_path}')

        self.check_server_disk_space()

        # check that requests are lists and that each list does not contain repeated values
        for k, v in param2requests.items():
            if not isinstance(v, list):
                raise TypeError('Values of param2requests must be lists')
            if len(v) != len(set(v)):  # otherwise each identical value will be assigned a unique param_name
                raise ValueError('Each requested parameter value must be unique')

        # ------------------------------- checks end

        if not no_upload:
            worker2ip = self.make_worker2ip()
        else:
            worker2ip = None

        # make list of hyper-parameter configurations to submit
        param2val_list = self.list_all_param2vals(param2requests)

        # copy extra folders to file server  (can be Python packages, which will be importable, or contain data)
        for p in extra_paths:
            src = str(p)
            dst = str(research_data_path / self.project_name / p.name)
            print_ludwig(f'Copying {src} to {dst}')
            copy_tree(src, dst)

        # add param_name to param2val
        print_ludwig('Assigning param_names...')
        for n, param2val in enumerate(param2val_list):
            old_or_new, param_name = self.logger.get_param_name(param2val)
            param2val['param_name'] = param_name
            print_ludwig(f'param2val {n + 1}/{len(param2val_list)} assigned to {old_or_new} {param_name}')

        # add reps
        param2val_list = self.add_reps(param2val_list, reps)

        # distribute (expensive) jobs approximately evenly across workers
        param2val_list = np.random.permutation(param2val_list)

        # split into chunks (one per node)
        worker_names = iter(np.random.permutation(config.SFTP.online_worker_names)) if worker is None else iter([worker])
        num_workers = 1 if worker is not None else self.num_online_workers
        for param2val_chunk in np.array_split(param2val_list, num_workers):
            try:
                worker_name = next(worker_names)  # distribute jobs across workers randomly
            except StopIteration:
                raise SystemExit(f'Using only {worker} because "worker" arg is not None.')
            #
            if len(param2val_chunk) == 0:
                print_ludwig(f'Not submitting to {worker_name}')
                continue

            # add to param2val
            base_name = self.make_job_base_name(worker_name)
            project_path = config.WorkerDirs.research_data / self.project_name
            for n, param2val in enumerate(param2val_chunk):
                # job_name
                job_name = f'{base_name}_num{n}'
                param2val['job_name'] = job_name
                # project_path - can be used to load data sets from shared drive
                param2val['project_path'] = str(project_path)
                # save_path - should be local (contents will be copied to shared drive after job completion)
                save_path = Path('runs') / param2val['param_name'] / job_name / config.Names.save_dir
                param2val['save_path'] = str(save_path)

            # save chunk to shared drive (after addition of job_name)
            p = project_path / f'{worker_name}_param2val_chunk.pkl'
            with p.open('wb') as f:
                pickle.dump(param2val_chunk, f)

            # console
            print()
            print_ludwig(f'Connecting to {worker_name}')
            for param2val in param2val_chunk:
                print(param2val)

            # prepare paths
            remote_path = f'{config.WorkerDirs.watched.name}/{src_name}'
            print_ludwig(f'Will upload {src_name} to {remote_path}')

            if no_upload:
                print_ludwig('Flag --upload set to False. Not uploading run.py.')
                continue

            # connect via sftp
            private_key_path = config.WorkerDirs.research_data / '.ludwig' / 'id_rsa'
            sftp = pysftp.Connection(username='ludwig',
                                     host=worker2ip[worker_name],
                                     private_key=str(private_key_path))

            sftp.makedirs(remote_path)
            sftp.put_r(localpath=src_name, remotepath=remote_path)
            sys.stdout.flush()

            # upload run.py
            run_file_name = f'run_{self.project_name}.py'
            sftp.put(localpath=run.__file__,
                     remotepath=f'{config.WorkerDirs.watched.name}/{run_file_name}')
            print_ludwig('Upload complete')

    def gen_param_ps(self,
                     param2requests: Dict[str, list],
                     runs_path: Optional[Path] = None,
                     label_params: List[str] = None,
                     label_n: bool = True,
                     verbose: bool = True):
        """
        Return path objects that point to folders with job results.
         Folders located in those paths are each generated with the same parameter configuration.
         Use this for retrieving data after a job has been completed
        """
        print_ludwig('Generating paths to jobs matching the following configuration:')
        print_ludwig(param2requests)
        print(flush=True)

        label_params = sorted(set([param for param, val in param2requests.items()
                                   if val != self.param2default[param]] + (label_params or [])))

        requested_param2vals = self.list_all_param2vals(param2requests)

        # check that research_data is mounted
        if not os.path.ismount(config.WorkerDirs.research_data):
            raise OSError(f'{config.WorkerDirs.research_data} is not mounted')

        # get + check path to runs
        if runs_path is None:
            runs_path = self.runs_path
        if not runs_path.exists():
            raise FileNotFoundError(f'{runs_path} does not exist.')

        # look for param_paths
        for param_path in runs_path.glob('param_*'):
            if verbose:
                print_ludwig(f'Checking {param_path}...')

            # load param2val
            with (param_path / 'param2val.yaml').open('r') as f:
                param2val = yaml.load(f, Loader=yaml.FullLoader)
            loaded_param2val = param2val.copy()
            del loaded_param2val['param_name']
            del loaded_param2val['job_name']

            # is match?
            if loaded_param2val in requested_param2vals:
                label_ = '\n'.join([f'{param}={param2val[param]}' for param in label_params])
                if label_n:
                    n = len(list(param_path.glob('*num*')))
                    label_ += f'\nn={n}'
                if verbose:
                    print_ludwig('Param2val matches')
                    print_ludwig(label_)
                yield param_path, label_
            else:
                if verbose:
                    print_ludwig('Params do not match')


