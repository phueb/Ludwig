import argparse
import importlib
from pathlib import Path
import sys
import subprocess
import psutil
import shutil
import datetime

import ludwig
from ludwig import print_ludwig
from ludwig import __version__
from ludwig.run import save_job_files


def run_on_host():
    """
    run jobs on the local host for testing/development
    """
    from ludwig import config as ludwig_config

    ludwig.try_mounting = False

    cwd = Path.cwd()
    project_name = cwd.name

    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--src', default=cwd.name.lower(), action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug', required=False,
                        help='Debugging.')
    parser.add_argument('-s', '--server', action='store_true', default=False, dest='server', required=False,
                        help='Use connection to server for loading data and saving results.')
    parser.add_argument('-f', '--first_only', action='store_true', default=False, dest='first_only', required=False,
                        help='Run first job and exit.')
    parser.add_argument('-mnt', '--mnt_path_name', default=None, action='store', dest='mnt_path_name',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')
    namespace = parser.parse_args()

    if not (cwd / namespace.src).is_dir():
        raise NotADirectoryError('Cannot find source code in {}.'.format(cwd / namespace.src))

    # import user's code
    print_ludwig('Looking for source code in:\n{}'.format(namespace.src))
    sys.path.append(str(cwd))
    job = importlib.import_module(namespace.src + '.job')
    params = importlib.import_module(namespace.src + '.params')
    config = importlib.import_module(namespace.src + '.config')

    if namespace.mnt_path_name:
        mnt_path = Path(namespace.mnt_path_name)
        if not mnt_path.exists():
            raise OSError(f'{mnt_path} does not exist. '
                          'Please set the correct path to your custom mount point.')
        else:
            ludwig.try_mounting = True

    # give user option to run job using a custom param2debug instead of param2default
    if namespace.debug:
        config.Global.debug = True

    # in case user does not have access to file server or there is no network connection
    if not namespace.server and not namespace.mnt_path_name:

        raise NotImplementedError  # TODO Need to implement modification of project_path and save_path

    # make client + logger
    from ludwig.client import Client  # import Client only after ludwig.try_mounting set to False
    client = Client(project_name, params.param2default)

    # iterate over jobs, and execute each in sequence
    for n, param2val in enumerate(client.list_all_param2vals(params.param2requests)):

        if namespace.debug:
            print_ludwig('Updating params.param2val with params.param2debug because debug=True')
            param2val.update(params.param2debug)

        # add param_name
        runs_path = ludwig_config.WorkerDirs.research_data / project_name / 'runs'
        _, param_name_suffix = client.logger.get_param_name(param2val, runs_path)
        param_name = f'not-ludwig_{param_name_suffix}'
        param2val['param_name'] = param_name
        print_ludwig(f'Assigned param_name={param_name}')
        # TODO no mechanism in place for protecting existing param folders locally - they are overwritten

        # add job_name
        time_of_init = datetime.datetime.now().strftime(ludwig_config.Time.format)
        base_name = '{}_{}'.format('local', time_of_init)
        job_name = '{}_num{}'.format(base_name, n)
        param2val['job_name'] = job_name

        # add project_path
        project_path = cwd
        param2val['project_path'] = project_path

        # add save_path - must not be on shared drive because contents are copied to shred drive at end of job
        param2val['save_path'] = Path('runs') / param_name / job_name / ludwig_config.Names.save_dir

        # prepare save_path
        save_path = param2val['save_path']
        if not save_path.exists():
            save_path.mkdir(parents=True)

        # execute job + save results
        series_list = job.main(param2val)
        save_job_files(param2val, series_list, runs_path)

        if namespace.first_only:
            raise SystemExit('Completed first job and exited because --first_only=True.')


def add_ssh_config():
    """
    append contents of /media/research_data/.ludwig/config to ~/.ssh/ludwig_config
    """
    from ludwig import config as ludwig_config

    src = ludwig_config.WorkerDirs.research_data / '.ludwig' / 'config'
    dst = Path().home() / '.ssh' / 'ludwig_config'  # do not overwrite existing config
    print_ludwig('Copying {} to {}'.format(src, dst))
    shutil.copy(src, dst)


def stats():  # TODO how to get stats of workers, not host? - use this on remote to check if a job can run immediately

    from ludwig import config as ludwig_config

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

    from ludwig import config as ludwig_config

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=ludwig_config.SFTP.online_worker_names, required=False,
                        help='The name of the worker the status of which is requested.')
    namespace = parser.parse_args()

    if namespace.worker is None:
        match_string = ' '.join([str(ludwig_config.WorkerDirs.stdout / (w + '.out'))
                                 for w in ludwig_config.SFTP.online_worker_names])
        tail_length = 1
        show_num_lines = len(ludwig_config.SFTP.online_worker_names)
    else:
        match_string = str(ludwig_config.WorkerDirs.stdout / (namespace.worker + ".out"))
        tail_length = 10
        show_num_lines = 10

    command = f'tail -n {tail_length} {match_string}'
    status_, output = subprocess.getstatusoutput(command)

    if status_ != 0:
        return 'Something went wrong. Check your access to {}'.format(ludwig_config.WorkerDirs.research_data)
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

    from ludwig.client import Client
    from ludwig import config as ludwig_config

    cwd = Path.cwd()
    project_name = cwd.name  # TODO test

    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--src', default=cwd.name.lower(), action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')

    parser.add_argument('-r', '--reps', default=1, action='store', dest='reps', type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50], required=False,
                        help='Number of times each job will be executed')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=ludwig_config.SFTP.online_worker_names, required=False,
                        help='Specify a single worker name if submitting to single worker only')
    parser.add_argument('-x', '--clear_runs', action='store_true', default=False, dest='clear_runs', required=False,
                        help='Delete all saved runs associated with current project on shared drive')

    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-mnt', '--mnt_path_name', default=None, action='store', dest='mnt_path_name',
                        required=False,
                        help='Specify where the shared drive is mounted on your system (if not /media/research_data).')

    # TODO add option to specify multiple workers - or specific "teams" of workers

    parser.add_argument('-e', '--extra_paths', nargs='*', default=[], action='store', dest='extra_paths',
                        required=False,
                        help='Paths to additional Python packages or data. ')
    parser.add_argument('-n', '--no-upload', action='store_true', dest='no_upload', required=False,
                        help='Whether to upload jobs to Ludwig. Set false for testing')
    namespace = parser.parse_args()

    if not (cwd / namespace.src).is_dir():
        raise NotADirectoryError('Cannot find source code in {}.'.format(cwd / namespace.src))

    # import user params
    print_ludwig('Looking for source code in:\n{}'.format(namespace.src))
    sys.path.append(str(cwd))
    params = importlib.import_module(namespace.src + '.params')

    # delete all runs in remote root
    if namespace.clear_runs:
        runs_path = ludwig_config.WorkerDirs.research_data / project_name / 'runs'
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

    # submit
    client = Client(project_name, params.param2default)
    client.submit(src_name=namespace.src,  # uploaded to workers
                  extra_paths=extra_paths,  # uploaded to shared drive not workers
                  param2requests=params.param2requests,
                  reps=namespace.reps,
                  no_upload=namespace.no_upload,
                  worker=namespace.worker,
                  mnt_path_name=namespace.mnt_path_name)