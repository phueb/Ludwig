import argparse
import pickle
import socket
from datetime import datetime
import yaml

from yourmodule import config
from yourmodule.params import param2requests, param2default
from yourmodule.job import main

hostname = socket.gethostname()


def run_on_cluster():
    """
    run multiple jobs on multiple LudwigCluster nodes.
    """
    p = config.RemoteDirs.root / '{}_param2val_chunk.pkl'.format(hostname)
    with p.open('rb') as f:
        param2val_chunk = pickle.load(f)
    for param2val in param2val_chunk:

        # execute job
        main(param2val)

        # write param2val to shared drive
        param2val_p = config.RemoteDirs.runs / param2val['param_name'] / 'param2val.yaml'
        if not param2val_p.exists():
            param2val_p['job_name'] = None
            with param2val_p.open('w', encoding='utf8') as f:
                yaml.dump(param2val, f, default_flow_style=False, allow_unicode=True)

    print('Finished all {} jobs at {}.'.format(config.LocalDirs.src.name, datetime.now()))
    print()


def run_on_host():
    """
    run jobs on the local host for testing/development
    """
    from ludwigcluster.utils import list_all_param2vals

    for param2val in list_all_param2vals(param2requests, param2default,
                                         update_d={'param_name': 'test', 'job_name': 'test'}):
        main(param2val)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', default=False, action='store_true', dest='local', required=False)
    namespace = parser.parse_args()
    if namespace.local:
        run_on_host()
    else:
        run_on_cluster()