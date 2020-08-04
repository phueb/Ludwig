import os
import argparse
import importlib
from pathlib import Path
import sys
import subprocess
from distutils.dir_util import copy_tree
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
from ludwig import configs


def add_ssh_config():
    """
    append contents of /media/research_data/.ludwig/config to ~/.ssh/ludwig_config
    """
    src = configs.WorkerDirs.research_data / '.ludwig' / 'config'
    dst = Path().home() / '.ssh' / 'ludwig_config'  # do not overwrite existing config
    print_ludwig('Copying {} to {}'.format(src, dst))
    shutil.copy(src, dst)


def status():
    """
    return filtered stdout (to which workers are printing) to get a sense of what workers are doing
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=configs.Remote.online_worker_names, required=False,
                        help='The name of the worker the status of which is requested.')
    parser.add_argument('-mnt', '--research_data', default=None, action='store', dest='research_data_path',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')
    namespace = parser.parse_args()

    if namespace.research_data_path:
        research_data_path = Path(namespace.research_data_path)
    else:
        research_data_path = Path(default_mnt_point) / configs.WorkerDirs.research_data.name

    stdout_path = research_data_path / configs.WorkerDirs.stdout.name

    if namespace.worker is None:
        workers = configs.Remote.online_worker_names
    else:
        workers = [namespace.worker]

    res = ''
    for w in workers:

        match_string = str(stdout_path / (w + ".out"))
        tail_length = 10_000

        command = f'tail -n {tail_length} {match_string}'
        status_, output = subprocess.getstatusoutput(command)

        if status_ != 0:
            return 'Something went wrong. Check your access to the shared drive. Try using --mnt flag.'

        lines = str(output).split('\n')
        lines_with_ludwig_status = [line for line in lines if 'Ludwig' in line]

        # collect strings
        try:
            res += lines_with_ludwig_status[-1]  # second to last shows status
        except IndexError:  # assume worker is busy
            res += f'{" ":>27} ({w.capitalize():<8}): Working on job'
        res += '\n'

    return res.strip('\n')


def submit():
    """
    run jobs locally or on Ludwig workers.

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
                        choices=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50],
                        required=False,
                        help='Number of times each job will be executed. To kill all jobs, use 0.')  # TODO test r 0 - it should kill all running jobs
    parser.add_argument('-m', '--minimal', action='store_true', default=False, dest='minimal',
                        required=False,
                        help='Run minimal parameter configuration for debugging.')
    parser.add_argument('-l', '--local', action='store_true', default=False, dest='local',
                        required=False,
                        help='Run on host')
    parser.add_argument('-i', '--isolated', action='store_true', default=False, dest='isolated',
                        required=False,
                        help='Do not connect to server. Only works when all data is available on client.')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=configs.Remote.online_worker_names,
                        required=False,
                        help='Specify a single worker name if submitting to single worker only')
    parser.add_argument('-g', '--group', default=None, action='store', dest='group',
                        choices=configs.Remote.group2workers.keys(),
                        required=False,
                        help='Specify a worker group')
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

    # ---------------------------------------------- checks

    assert not (namespace.local and namespace.isolated)
    assert not (namespace.extra_paths and namespace.isolated)

    # ---------------------------------------------- paths (relative to client, except when stated otherwise)

    if namespace.research_data_path:
        research_data_path = Path(namespace.research_data_path)
    else:
        research_data_path = Path(default_mnt_point) / configs.WorkerDirs.research_data.name

    remote_project_path = research_data_path / project_name

    if namespace.isolated:
        runs_path = cwd / 'runs'
    else:
        runs_path = remote_project_path / 'runs'

    src_path = cwd / namespace.src

    # ------------------------------------------------ user code

    # import user params + job
    print_ludwig('Trying to import source code from:\n{}'.format(src_path))
    sys.path.append(str(cwd))
    user_params = importlib.import_module(src_path.name + '.params')
    if namespace.local or namespace.isolated:  # no need to import job when not executed locally
        user_job = importlib.import_module(src_path.name + '.job')

    # ------------------------------------------------ checks

    if not namespace.isolated:
        if not os.path.ismount(str(research_data_path)):
            raise OSError(f'{research_data_path} is not mounted')

    if not src_path.exists():
        raise NotADirectoryError(f'Cannot find source code in {src_path}.')

    # check that requests are lists and that each list does not contain repeated values
    for k, v in user_params.param2requests.items():
        if not isinstance(v, list):
            raise TypeError('Value of param2requests["{}"] must be a list'.format(k))
        for vi in v:
            if isinstance(vi, list):  # tuples can be members of a set (they are hashable) but not lists
                raise TypeError('Inner collections in param2requests must be of type tuple, not list')
        if len(v) != len(set(v)):  # otherwise each identical value will be assigned a unique param_name
            raise ValueError('Each requested parameter value must be unique')

    # check that there are no lists (only tuples) in param2default
    for k, v in user_params.param2default.items():
        if isinstance(v, list):  # tuples can be members of a set (they are hashable) but not lists
            raise TypeError('Type list is not allowed in param2default. Convert any lists to tuples.')

    # ---------------------------------------------

    # are additional source code files required? (do this before killing active jobs)
    # these can be Python packages, which will be importable, or contain data.
    # extra_paths is only allowed to be non-empty if not --local
    for extra_path in namespace.extra_paths:
        p = Path(extra_path)
        if not p.is_dir():
            raise NotADirectoryError('{} is not a directory'.format(p))
        src = str(extra_path)
        dst = str(remote_project_path / p.name)
        print_ludwig(f'Copying {src} to {dst}')
        copy_tree(src, dst)

    uploader = Uploader(remote_project_path, src_path.name)

    # delete job instructions for worker saved on server (do this before uploader.to_disk() )
    for pkl_path in remote_project_path.glob(f'*.pkl'):
        pkl_path.unlink()

    if namespace.group is None:
        random.shuffle(configs.Remote.online_worker_names)
        workers_cycle = cycle(configs.Remote.online_worker_names)
    else:
        workers_cycle = cycle(configs.Remote.group2workers[namespace.group])
        print(f'Using workers in group={namespace.group}')

    # ---------------------------------------------------

    if namespace.minimal:
        print_ludwig('Using minimal (debug) parameter configuration')
        param2val = user_params.param2default.copy()
        param2val.update(user_params.param2debug)
        param2val_list = [param2val]
    else:
        param2val_list = gen_all_param2vals(user_params.param2requests,
                                            user_params.param2default)
    # iterate over unique jobs
    num_new = 0
    workers_with_jobs = set()
    for param2val in param2val_list:

        # make job
        job = Job(param2val)

        # get param_name - always try to use an existing param_name even if clear_runs == True,
        # because this provides constancy in that parameter configurations always receive the same param_name,
        # which allows for hard-coding param_names in user code.
        # but hard-coding is not recommended, because constancy is broken when runs are manually cleared.
        job.update_param_name(runs_path, num_new)

        # add project_path
        if namespace.local:
            job.param2val['project_path'] = str(remote_project_path)
        elif namespace.isolated:
            job.param2val['project_path'] = str(cwd)
        else:
            job.param2val['project_path'] = str(configs.WorkerDirs.research_data / project_name)

        # allow exit if requested parameter configuration already exists requested number of times?
        # do counting with --local, because behavior when --local should be identical to behavior of Ludwig worker
        if namespace.minimal or namespace.isolated or namespace.clear_runs:
            num_needed = namespace.reps
        else:
            num_needed = job.calc_num_needed(runs_path, namespace.reps)

        # replicate each job
        for rep_id in range(num_needed):

            # add job_name and save_path
            job.update_job_name(rep_id)

            # if running locally, execute job now + cleanup
            if namespace.local or namespace.isolated:
                series_list = user_job.main(job.param2val)
                save_job_files(job.param2val, series_list, runs_path)
                # remove old parents of save_paths - these should always be empty
                for p in cwd.glob('param*'):
                    print(f'Removing {p}')
                    shutil.rmtree(p)

            # if running on Ludwig, save worker instructions to shared drive
            else:

                worker = namespace.worker or next(workers_cycle)
                workers_with_jobs.add(worker)
                uploader.to_disk(job, worker)

        num_new += int(job.is_new)

        if namespace.first_only:
            raise SystemExit('Exiting loop after first job because --first_only=True.')

    # exit ?
    if namespace.no_upload:
        print_ludwig('Flag --upload set to False. Not uploading run.py.')
        return
    elif namespace.local or namespace.isolated:
        return

    # kill running jobs on workers? (do this before removing runs folders).
    # trigger worker without job instructions: kills existing job with matching project_name
    for worker in set(configs.Remote.online_worker_names).difference(workers_with_jobs):
        uploader.kill_jobs(worker)

    # delete existing runs on shared drive?
    if namespace.clear_runs:
        for param_path in runs_path.glob('*param*'):
            print_ludwig('Removing\n{}'.format(param_path))
            sys.stdout.flush()
            shutil.rmtree(str(param_path))

    # upload = start jobs
    for worker in workers_with_jobs:
        uploader.start_jobs(worker)

    print('Submitted jobs to:')
    for w in workers_with_jobs:
        print(w)
