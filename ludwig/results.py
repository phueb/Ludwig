from itertools import cycle
from pathlib import Path
import datetime
import numpy as np
import yaml
import os
from typing import List, Dict, Optional, Any, Tuple

from ludwig import config
from ludwig import print_ludwig


class Results:
    """
    quickly retrieve results from jobs submitted to Ludwig
    """

    def __init__(self,
                 project_name: str,
                 param2default: Dict[str, Any],
                 ):
        self.project_name = project_name
        self.param2default = param2default

    def gen_param_ps(self,
                     param2requests: Dict[str, list],
                     runs_path: Optional[Path] = None,
                     label_params: List[str] = None,
                     label_n: bool = True,
                     verbose: bool = True):
        """
        Return path objects that point to folders with job results.
         Folders located in those paths are each generated with the same parameter configuration.
         Use this for retrieving data after a job has been completed
        """
        print_ludwig('Generating paths to jobs matching the following configuration:')
        print_ludwig(param2requests)
        print(flush=True)

        label_params = sorted(set([param for param, val in param2requests.items()
                                   if val != self.param2default[param]] + (label_params or [])))

        requested_param2vals = self.list_all_param2vals(param2requests)

        # check that research_data is mounted
        if not os.path.ismount(config.WorkerDirs.research_data):
            raise OSError(f'{config.WorkerDirs.research_data} is not mounted')

        # get + check path to runs
        if runs_path is None:
            runs_path = config.WorkerDirs.research_data / self.project_name / 'runs'
        if not runs_path.exists():
            raise FileNotFoundError(f'{runs_path} does not exist.')

        # look for param_paths
        for param_path in runs_path.glob('param_*'):
            if verbose:
                print_ludwig(f'Checking {param_path}...')

            # load param2val
            with (param_path / 'param2val.yaml').open('r') as f:
                param2val = yaml.load(f, Loader=yaml.FullLoader)
            loaded_param2val = param2val.copy()
            del loaded_param2val['param_name']
            del loaded_param2val['job_name']

            # is match?
            if loaded_param2val in requested_param2vals:
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


