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

        # check if host is down - do this before any computation
        assert config.RemoteDirs.runs.exists()  # this throws error if host is down

        # execute job
        dfs = main(param2val)  # name the returned dataframes using 'name' attribute

        if config.Eval.debug:
            for df in dfs:
                print(df.name)
                print(df)
            raise SystemExit('Debugging: Not saving results')

        # save dfs
        dst = config.RemoteDirs.runs / param2val['param_name'] / param2val['job_name']
        if not dst.exists():
            dst.mkdir(parents=True)
        for df in dfs:
            with (dst / '{}.csv'.format(df.name)).open('w') as f:
                df.to_csv(f, index=True)

        # write param2val to shared drive
        param2val_p = config.RemoteDirs.runs / param2val['param_name'] / 'param2val.yaml'
        print('Saving param2val to:\n{}\n'.format(param2val_p))
        if not param2val_p.exists():
            param2val['job_name'] = None
            with param2val_p.open('w', encoding='utf8') as f:
                yaml.dump(param2val, f, default_flow_style=False, allow_unicode=True)

    print('Finished all {} jobs at {}.'.format(config.LocalDirs.src.name, datetime.now()))
    print()


def run_on_host():
    """
    run jobs on the local host for testing/development
    """
    from ludwigcluster.client import Client

    project_name = config.LocalDirs.src.name
    client = Client(project_name, param2default)
    for param2val in client.list_all_param2vals(param2requests,
                                                update_d={'param_name': 'test', 'job_name': 'test'}):
        main(param2val)
        raise SystemExit('Finished running first job.\n'
                         'No further jobs will be run as results would be over-written')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', default=False, action='store_true', dest='local', required=False)
    parser.add_argument('-d', default=False, action='store_true', dest='debug', required=False)
    namespace = parser.parse_args()
    if namespace.debug:
        config.Eval.debug = True
    #
    if namespace.local:
        run_on_host()
    else:
        run_on_cluster()