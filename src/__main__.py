import argparse
import importlib
from pathlib import Path
import sys
import subprocess
import psutil
import shutil

from src.client import Client
from src import config as ludwig_config
from src.config import SFTP


def run_on_host():
    """
    run jobs on the local host for testing/development
    """

    cwd = Path.cwd()

    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--src', default=cwd.name.lower(), action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug', required=False,
                        help='Debugging.')
    namespace = parser.parse_args()

    if not (cwd / namespace.src).is_dir():
        raise NotADirectoryError('Cannot find source code in {}.'.format(cwd / namespace.src))

    # import user's code
    print('Looking for source code in:\n{}'.format(namespace.src))
    sys.path.append(str(cwd))
    job = importlib.import_module(namespace.src + '.job')
    params = importlib.import_module(namespace.src + '.params')
    config = importlib.import_module(namespace.src + '.config')

    if namespace.debug:
        config.Global.debug = True  # this results in using param2debug instead of param2default

    # iterate over jobs, and execute each in sequence
    project_name = config.LocalDirs.root.name
    client = Client(project_name, params.param2default)
    for param2val in client.list_all_param2vals(params.param2requests,
                                                update_d={'param_name': 'test', 'job_name': 'test'}):

        if namespace.debug:
            print('Updating params.param2val with params.param2debug because debug=True')
            param2val.update(params.param2debug)

        job.main(param2val)

        if namespace.debug:
            raise SystemExit('Completed first job and exited because debug=True.')

    # TODO running locally doesn't save data as implemented - should this be an option?
    # TODO if so, maybe change the naming convention from "test" to "local" and assign each a time_of_init


def stats():  # TODO how to get stats of workers, not host?
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

    return ps[:ludwig_config.CLI.num_top_processes]


def status():
    """
    return filtered stdout (to which workers are printing) to get a sense of what workers are doing
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--worker', default='*', action='store', dest='worker',
                        choices=SFTP.worker_names, required=False,
                        help='The name of the worker the status of which is requested.')
    namespace = parser.parse_args()

    command = 'cat {}/{}.out'.format(ludwig_config.Dirs.stdout, namespace.worker)

    status_, output = subprocess.getstatusoutput(command)
    if status_ != 0:
        return 'Something went wrong. Check your access to {}'.format(ludwig_config.Dirs.research_data)
    lines = str(output).split('\n')
    res = '\n'.join([line for line in lines
                     if 'Ludwig' in line][-ludwig_config.CLI.num_stdout_lines:])
    return res


def submit():
    """
    This script should be called in root directory of the Python project.
    If not specified via CL arguments, it will try to import src.config and src.params.
    src.config is where this script will try to find the name of your project
    src.params is where this script will try to find the parameters with which to execute your jobs.
    """

    cwd = Path.cwd()

    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--src', default=cwd.name.lower(), action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')

    parser.add_argument('-r', '--reps', default=1, action='store', dest='reps', type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50], required=False,
                        help='Number of times each job will be executed')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=SFTP.worker_names, required=False,
                        help='Specify a single worker name if submitting to single worker only')
    parser.add_argument('-x', '--clear_runs', action='store_true', default=False, dest='clear_runs', required=False)


    # TODO test custom mount point on MacOs

    parser.add_argument('-mnt', '--mnt_path_name', default=None, action='store', dest='mnt_path_name',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')

    # TODO add option to specify multiple workers - or specific "teams" of workers

    parser.add_argument('-c', '--extra_folders', nargs='*', default=[], action='store', dest='extra_folders',
                        required=False,
                        help='Paths to additional Python packages or data. ')
    parser.add_argument('-t', '--test', action='store_true', dest='test', required=False,
                        help='For debugging/testing purpose only')
    parser.add_argument('-p', '--prepare_data', action='store_true', default=False, dest='prepare_data', required=False,
                        help='Whether to save results of pre-processing job to file-server')
    namespace = parser.parse_args()

    if not (cwd / namespace.src).is_dir():
        raise NotADirectoryError('Cannot find source code in {}.'.format(cwd / namespace.src))

    print('Looking for source code in:\n{}'.format(namespace.src))
    sys.path.append(str(cwd))
    job = importlib.import_module(namespace.src + '.job')
    params = importlib.import_module(namespace.src + '.params')
    config = importlib.import_module(namespace.src + '.config')

    # delete all runs in remote root
    if namespace.clear_runs:
        for param_p in config.RemoteDirs.runs.glob('*param*'):
            print('Removing\n{}'.format(param_p))
            sys.stdout.flush()
            shutil.rmtree(str(param_p))

    # prepare any data and save pickle to shared drive - do this only once - import this function from jobs module
    if namespace.prepare_data:
        print('Starting to prepare data')
        job.prepare_data()
        print('Completed preparing data')
    else:
        print('WARNING: Not preparing any data')

    # are additional source code files required?
    extra_folder_ps = []
    for extra_folder in namespace.extra_folders:
        p = Path(extra_folder)
        if not p.is_dir():
            raise NotADirectoryError('{} is not a directory'.format(p))
        else:
            extra_folder_ps.append(p)

    # submit
    project_name = config.RemoteDirs.root.name
    client = Client(project_name, params.param2default)
    client.submit(src_p=config.LocalDirs.src,  # uploaded to workers
                  extra_folder_ps=extra_folder_ps,  # uploaded to shared drive not workers
                  param2requests=params.param2requests,
                  reps=namespace.reps,
                  test=namespace.test,
                  worker=namespace.worker,
                  mnt_path_name=namespace.mnt_path_name)