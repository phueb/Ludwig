import argparse
import importlib
from pathlib import Path

from ludwigcluster.client import Client
from ludwigcluster.config import SFTP


def main():
    """
    This script should be called in root directory of the Python project.
    If not specified via CL arguments, it will try to import your_module.config and your_module.params.
    module.config is where this script will try to find the name of your project
    module.params is where this script will try to find the parameters with which to execute your jobs.
    """

    cwd = Path.cwd()
    print('Current working directory:\n{}'.format(cwd))
    src_path = cwd / cwd.name.lower()  # best guess where source code is located (e.g. modules: params and config)
    print('Looking for source code in folder with name "{}"'.format(src_path))
    if not src_path.exists():
        raise SystemExit('Guessed path to source code does not exist.\n'
                         'Please specify path to source code manually.')

    # parse cmd-line args
    parser = argparse.ArgumentParser()

    # TODO do not require  -c and -pr ; as default try to find modules in cwd

    parser.add_argument('-src', '--src', default=src_path.name, action='store', dest='src',
                        required=False,
                        help='Specify path to your source code.')

    parser.add_argument('-r', '--reps', default=2, action='store', dest='reps', type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50], required=False,
                        help='Number of replications to train per hyper-param configuration')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=SFTP.worker_names, required=False,
                        help='Specify a single worker name if submitting to single worker only')

    # TODO add option to specify multiple workers - or specific "teams" of workers

    parser.add_argument('-s', '--skip_data', default=False, action='store_true', dest='skip_data', required=False,
                        help='Whether or not to skip uploading data to file-server. ')
    parser.add_argument('-t', '--test', action='store_true', dest='test', required=False,
                        help='For debugging/testing purpose only')
    parser.add_argument('-p', '--prepare_data', action='store_true', default=False, dest='prepare_data', required=False,
                        help='Whether to save results of pre-processing job to file-server')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug', required=False,
                        help='Debugging. Minimal param configuration')
    namespace = parser.parse_args()

    if namespace.debug:
        print('WARNING: Debugging is on.')

    job    = importlib.import_module(namespace.src + '.job')
    params = importlib.import_module(namespace.src + '.params')
    config = importlib.import_module(namespace.src + '.config')

    # prepare any data and save pickle to shared drive - do this only once - import this function from jobs module
    if namespace.prepare_data:
        print('Starting to prepare data')
        job.prepare_data()
        print('Completed preparing data')
    else:
        print('WARNING: Not preparing any data')

    # submit to cluster
    data_dirs = [] if not namespace.skip_data else []  # this data is copied to file server not workers
    project_name = config.RemoteDirs.root.name
    client = Client(project_name, params.param2default)
    client.submit(src_ps=[config.LocalDirs.src],
                  data_ps=[config.LocalDirs.root / d for d in data_dirs],
                  param2requests=params.param2requests,
                  reps=namespace.reps,
                  test=namespace.test,
                  worker=namespace.worker)


if __name__ == '__main__':
    main()