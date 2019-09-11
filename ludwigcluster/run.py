import pickle
import socket
import yaml
import pandas as pd
import importlib
from pathlib import Path


def run_on_cluster():
    """
    run multiple jobs on on a single LudwigCluster machine.
    """

    p = config.RemoteDirs.root / '{}_param2val_chunk.pkl'.format(hostname)
    with p.open('rb') as f:
        param2val_chunk = pickle.load(f)
    for param2val in param2val_chunk:

        # check if host is down - do this before any computation
        assert config.RemoteDirs.runs.exists()  # this throws error if host is down

        # execute job
        dfs = job.main(param2val)  # name the returned dataframes using 'name' attribute

        if config.Global.debug:
            for df in dfs:
                print(df.name)
                print(df)
            raise SystemExit('Debugging: Not saving results')

        # save dfs
        dst = config.RemoteDirs.runs / param2val['param_name'] / param2val['job_name']
        if not dst.exists():
            dst.mkdir(parents=True)
        for df in dfs:
            if not isinstance(df, pd.DataFrame):
                print('WARNING: Object returned by job is not a pandas.DataFrame object.')
                continue
            with (dst / '{}.csv'.format(df.name)).open('w') as f:
                df.to_csv(f, index=True)

        # write param2val to shared drive
        param2val_p = config.RemoteDirs.runs / param2val['param_name'] / 'param2val.yaml'
        print('Saving param2val to:\n{}\n'.format(param2val_p))
        if not param2val_p.exists():
            param2val['job_name'] = None
            with param2val_p.open('w', encoding='utf8') as f:
                yaml.dump(param2val, f, default_flow_style=False, allow_unicode=True)


if __name__ == '__main__':

    # import source code
    # get name of folder containing source code from name of file
    src_path_name = Path(__file__).stem.replace('run_', '')
    config = importlib.import_module('{}.config'.format(src_path_name))
    job = importlib.import_module('{}.job'.format(src_path_name))

    hostname = socket.gethostname()

    run_on_cluster()