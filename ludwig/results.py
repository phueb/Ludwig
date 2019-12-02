from pathlib import Path
import yaml
import os
from typing import List, Dict, Optional, Any

from ludwig import print_ludwig
from ludwig import config
from ludwig.requests import gen_all_param2vals
from ludwig.paths import default_mnt_point


def gen_param_paths(project_name: str,
                    param2requests: Dict[str, list],
                    param2default: Dict[str, Any],
                    runs_path: Optional[Path] = None,
                    research_data_path: Optional[Path] = None,
                    label_params:   Optional[List[str]] = None,
                    isolated: bool = False,
                    label_n: bool = True,
                    verbose: bool = True):
    """
    Return path objects that point to folders with job results.
     Folders located in those paths are each generated with the same parameter configuration.
     Use this for retrieving data after a job has been completed
    """

    # --------------------------------------------------------  paths

    if research_data_path:
        research_data_path = Path(research_data_path)
    else:
        research_data_path = Path(default_mnt_point) / config.WorkerDirs.research_data.name

    if isolated:
        project_path = Path.cwd()
    else:
        project_path = research_data_path / project_name

    if not runs_path:
        runs_path = project_path / 'runs'

    # check that research_data is mounted
    if not os.path.ismount(research_data_path):
        raise OSError(f'{research_data_path} is not mounted')

    # get + check path to runs
    if runs_path is None:
        runs_path = research_data_path / project_name / 'runs'
    if not runs_path.exists():
        raise FileNotFoundError(f'{runs_path} does not exist.')

    # ------------------------------------------------------- prepare params

    label_params = sorted(set([param for param, val in param2requests.items()
                               if val != param2default[param]] + (label_params or [])))

    requested_param2vals = list(gen_all_param2vals(param2requests, param2default))

    print_ludwig('Looking for the following parameter configurations:')
    num_requested = 0
    for requested_param2val in requested_param2vals:
        print(sorted(requested_param2val.items()))
        num_requested += 1

    # look for param_paths
    num_found = 0
    for param_path in runs_path.glob('param_*'):
        if verbose:
            print_ludwig(f'Checking {param_path}...')

        # load param2val
        with (param_path / 'param2val.yaml').open('r') as f:
            param2val = yaml.load(f, Loader=yaml.FullLoader)
        loaded_param2val = param2val.copy()

        for param_name in config.Constants.added_param_names:
            try:
                del loaded_param2val[param_name]
            except KeyError:  # Ludwig < v2.0
                pass

        # is match?
        if loaded_param2val in requested_param2vals:
            num_found += 1
            label_ = '\n'.join([f'{param}={param2val[param]}' for param in label_params])
            if label_n:
                n = len(list(param_path.glob('*num*')))
                label_ += f'\nn={n}'
            if verbose:
                print_ludwig('Param2val matches')
                print_ludwig(label_)
            yield param_path, label_
        else:
            if verbose:
                print_ludwig('Params do not match')

    if num_requested != num_found:
        raise SystemExit(f'Found {num_found} but requested {num_requested}')


