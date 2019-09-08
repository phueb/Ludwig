import argparse

from ludwigcluster.client import Client
from ludwigcluster.config import SFTP

from your_module.params import param2requests, param2default
from your_module import config
from your_module.job import pre_processing_job


def main():
    # parse cmd-line args
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reps', default=2, action='store', dest='reps', type=int,
                        choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50], required=False,
                        help='Number of replications to train per hyper-param configuration')
    parser.add_argument('-w', '--worker', default=None, action='store', dest='worker',
                        choices=SFTP.worker_names, required=False,
                        help='Specify a single worker name if submitting to single worker only')

    # TODO add option to specify multiple workers

    parser.add_argument('-s', '--skip_data', default=False, action='store_true', dest='skip_data', required=False,
                        help='Whether or not to skip uploading data to file-server. ')
    parser.add_argument('-t', '--test', action='store_true', dest='test', required=False,
                        help='For debugging/testing purpose only')
    parser.add_argument('-p', '--preprocess', action='store_true', default=False, dest='preprocess', required=False,
                        help='Whether to save results of pre-processing job to file-server')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug', required=False,
                        help='Debugging. Minimal param configuration')
    namespace = parser.parse_args()

    # preprocess any data and save pickle to file server
    if namespace.preprocess:
        pre_processing_job()

    # submit to cluster
    data_dirs = [] if not namespace.skip_data else []  # this data is copied to file server not workers
    project_name = config.RemoteDirs.root.name
    client = Client(project_name, param2default)
    client.submit(src_ps=[config.LocalDirs.src],
                  data_ps=[config.LocalDirs.root / d for d in data_dirs],
                  param2requests=param2requests,
                  reps=namespace.reps,
                  test=namespace.test,
                  worker=namespace.worker)


if __name__ == '__main__':
    main()