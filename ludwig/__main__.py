import os
import argparse
import importlib
from pathlib import Path
import sys
import subprocess
from distutils.dir_util import copy_tree
import psutil
import shutil
import random
from itertools import cycle

from ludwig import print_ludwig
from ludwig import __version__
from ludwig.requests import gen_all_param2vals
from ludwig.job import Job
from ludwig.paths import default_mnt_point
from ludwig.run import save_job_files
from ludwig.uploader import Uploader
from ludwig import config


def add_ssh_config():
    """
    append contents of /media/research_data/.ludwig/config to ~/.ssh/ludwig_config
    """
    from ludwig import config as ludwig_config

    src = ludwig_config.WorkerDirs.research_data / '.ludwig' / 'config'
    dst = Path().home() / '.ssh' / 'ludwig_config'  # do not overwrite existing config
    print_ludwig('Copying {} to {}'.format(src, dst))
    shutil.copy(src, dst)


def stats():

    ps = []
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
            pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
            ps.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort by 'vms' (virtual memory usage)
    ps = sorted(ps, key=lambda p: p['vms'], reverse=True)

    return ps[:config.CLI.num_top_processes]


def status():
    """
    return filtered stdout (to which workers are printing) to get a sense of what workers are doing
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=config.Submit.online_worker_names, required=False,
                        help='The name of the worker the status of which is requested.')
    parser.add_argument('-mnt', '--research_data', default=None, action='store', dest='research_data_path',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')
    namespace = parser.parse_args()

    if namespace.research_data_path:
        research_data_path = Path(namespace.research_data_path)
    else:
        research_data_path = Path(default_mnt_point) / config.WorkerDirs.research_data.name

    stdout_path = research_data_path / config.WorkerDirs.stdout.name

    if namespace.worker is None:
        match_string = ' '.join([str(stdout_path / (w + '.out'))
                                 for w in config.Submit.online_worker_names])
        tail_length = 1
        show_num_lines = len(config.Submit.online_worker_names)
    else:
        match_string = str(stdout_path / (namespace.worker + ".out"))
        tail_length = 10
        show_num_lines = 10

    command = f'tail -n {tail_length} {match_string}'
    status_, output = subprocess.getstatusoutput(command)

    if status_ != 0:
        return 'Something went wrong. Check your access to the shared drive. Try using --mnt flag.'
    lines = str(output).split('\n')
    show_lines = [line for line in lines if 'Ludwig' in line][-show_num_lines:]
    if show_lines:
        res = '\n'.join(show_lines)
    else:  # the string 'Ludwig' is not found in the last section of stdout, so assume user project is printing output
        res = 'Busy working on jobs'
    return res


def submit():
    """
    This script should be called in root directory of the Python project.
    If not specified via CL arguments, it will try to import src.params.
    src.params is where this script will try to find the parameters with which to execute your jobs.
    """

    cwd = Path.cwd()
    project_name = cwd.name

    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--src', default=cwd.name.lower(), action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')
    parser.add_argument('-r', '--reps', default=1, action='store', dest='reps', type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50],
                        required=False,
                        help='Number of times each job will be executed')
    parser.add_argument('-m', '--minimal', action='store_true', default=False, dest='minimal',
                        required=False,
                        help='Run minimal parameter configuration for debugging.')
    parser.add_argument('-l', '--local', action='store_true', default=False, dest='local',
                        required=False,
                        help='Run on host')
    parser.add_argument('-i', '--isolated', action='store_true', default=False, dest='isolated',
                        required=False,
                        help='Do not connect to server. Use this only when all daa is available')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=config.Submit.online_worker_names,
                        required=False,
                        help='Specify a single worker name if submitting to single worker only')
    parser.add_argument('-x', '--clear_runs', action='store_true', default=False, dest='clear_runs',
                        required=False,
                        help='Delete all saved runs associated with current project on shared drive')
    parser.add_argument('-f', '--first_only', action='store_true', default=False, dest='first_only',
                        required=False,
                        help='Run first job and exit.')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-mnt', '--research_data', default=None, action='store', dest='research_data_path',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')
    parser.add_argument('-e', '--extra_paths', nargs='*', default=[], action='store', dest='extra_paths',
                        required=False,
                        help='Paths to additional Python packages or data. ')
    parser.add_argument('-n', '--no-upload', action='store_true', dest='no_upload',
                        required=False,
                        help='Whether to upload jobs to Ludwig. Set false for testing')
    namespace = parser.parse_args()

    # ---------------------------------------------- paths

    if namespace.research_data_path:
        research_data_path = Path(namespace.research_data_path)
    else:
        research_data_path = Path(default_mnt_point) / config.WorkerDirs.research_data.name

    if namespace.isolated:
        project_path = cwd
    else:
        project_path = research_data_path / project_name

    runs_path = project_path / 'runs'

    src_path = cwd / namespace.src

    # ------------------------------------------------ user code

    # import user params + job
    print_ludwig('Trying to import source code from:\n{}'.format(src_path))
    sys.path.append(str(cwd))
    user_params = importlib.import_module(src_path.name + '.params')
    user_job = importlib.import_module(src_path.name + '.job')

    # ------------------------------------------------ checks

    if not namespace.isolated:
        if not os.path.ismount(str(research_data_path)):
            raise SystemError(f'Failed to mount {research_data_path}')

    assert not (namespace.extra_paths and namespace.local), 'Do not use  both --extra_paths and --local'

    if not src_path.exists():
        raise NotADirectoryError(f'Cannot find source code in {src_path}.')

    if not research_data_path.exists():
        raise OSError(f'{research_data_path} does not exist. '
                      'Please set the correct path to your custom mount point.')

    # check that requests are lists and that each list does not contain repeated values
    for k, v in user_params.param2requests.items():
        if not isinstance(v, list):
            raise TypeError('Values of param2requests must be lists')
        if len(v) != len(set(v)):  # otherwise each identical value will be assigned a unique param_name
            raise ValueError('Each requested parameter value must be unique')

    # ---------------------------------------------

    # delete existing runs
    if namespace.clear_runs:
        for param_path in runs_path.glob('*param*'):
            print_ludwig('Removing\n{}'.format(param_path))
            sys.stdout.flush()
            shutil.rmtree(str(param_path))

    # are additional source code files required?
    extra_paths = []
    for extra_path in namespace.extra_paths:
        p = Path(extra_path)
        if not p.is_dir():
            raise NotADirectoryError('{} is not a directory'.format(p))
        else:
            extra_paths.append(p)

    # copy extra folders to file server.
    # these can be Python packages, which will be importable, or contain data.
    # extra_paths is only allowed to be non-empty if not --local
    for extra_path in extra_paths:
        src = str(extra_path)
        dst = str(project_path / extra_path.name)
        print_ludwig(f'Copying {src} to {dst}')
        copy_tree(src, dst)

    uploader = Uploader(project_path, src_path.name)

    random.shuffle(config.Submit.online_worker_names)
    online_workers = cycle(config.Submit.online_worker_names)

    # ---------------------------------------------------

    # iterate over unique jobs
    for param2val in gen_all_param2vals(user_params.param2requests, user_params.param2default):

        # use minimal configuration only after param2val has been generated
        if namespace.minimal:
            print_ludwig('Using minimal (debug) parameter configuration')
            param2val.update(user_params.param2debug)

        # assign the same worker to each rep of the same job
        worker = namespace.worker or next(online_workers)

        job = Job(param2val, project_path)
        for rep_id in range(job.calc_num_needed(namespace.reps, unittest=False)):
            job.update_job_name(rep_id)
            if namespace.local or namespace.isolated:
                save_path = param2val['save_path']
                if not save_path.exists():
                    save_path.mkdir(parents=True)
                job.param2val['project_path'] = project_path
                job.param2val['param_name'] += config.Constants.not_ludwig
                job.param2val['job_name'] += config.Constants.not_ludwig
                series_list = user_job.main(job.param2val)
                save_job_files(job.param2val, series_list, runs_path)
            else:
                job.param2val['project_path'] = config.WorkerDirs.research_data / project_name
                uploader.upload(job, worker, namespace.no_upload)

        if namespace.first_only:
            raise SystemExit('Exited after first job because --first_only=True.')
