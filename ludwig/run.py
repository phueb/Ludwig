import pickle
import socket
import yaml
import pandas as pd
import importlib
from pathlib import Path
import sys
from typing import Dict, Any

# do not import ludwig here - this file is run on Ludwig workers


def save_job_files(param2val: Dict[str, Any],
                   series_list: list,
                   runs_path: Path,
                   ) -> None:

    if not series_list:
        print('WARNING: Job did not return any results')

    # save series_list
    dst = runs_path / param2val['param_name'] / param2val['job_name']
    if not dst.exists():
        dst.mkdir(parents=True)
    for series in series_list:
        if not isinstance(series, pd.Series):
            print('WARNING: Object returned by job must be a pandas.Series.')
            continue
        with (dst / '{}.csv'.format(series.name)).open('w') as f:
            series.to_csv(f, index=True, header=[series.name])  # cannot name the index with "header" arg

    # save param2val
    param2val_p = runs_path / param2val['param_name'] / 'param2val.yaml'
    print('Saving param2val to:\n{}\n'.format(param2val_p))
    if not param2val_p.exists():
        param2val_p.parent.mkdir(exist_ok=True)
        param2val['job_name'] = None
        with param2val_p.open('w', encoding='utf8') as f:
            yaml.dump(param2val, f, default_flow_style=False, allow_unicode=True)


def run_jobs_on_ludwig_worker():
    """
    run multiple jobs on on a single worker.
    """

    p = config.RemoteDirs.root / '{}_param2val_chunk.pkl'.format(hostname)
    with p.open('rb') as f:
        param2val_chunk = pickle.load(f)
    for param2val in param2val_chunk:

        # check if host is down - do this before any computation
        assert config.RemoteDirs.runs.exists()  # this throws error if host is down

        # execute job
        series_list = job.main(param2val)  # name the returned series using 'name' attribute

        # save results
        save_job_files(param2val, series_list, runs_path=config.RemoteDirs.runs)


if __name__ == '__main__':

    # get name of folder containing source code from name of file
    src_path_name = Path(__file__).stem.replace('run_', '')

    # import config for user's project
    config = importlib.import_module('{}.config'.format(src_path_name))

    # allow import of modules in root directory of project - e.g. childeshub
    path_to_remote_project_root = str(config.RemoteDirs.root)
    sys.path.append(path_to_remote_project_root)

    # import user's job to execute
    job = importlib.import_module('{}.job'.format(src_path_name))

    hostname = socket.gethostname()

    run_jobs_on_ludwig_worker()