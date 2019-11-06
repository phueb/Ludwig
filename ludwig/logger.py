import yaml
import shutil
from typing import Optional, Dict, Tuple, Any
from pathlib import Path

from ludwig import config


class Logger:
    """
    in-memory log for keeping track of which jobs have completed (and which have the same param2vals)
    """

    def __init__(self, project_name):
        self.project_name = project_name
        if not (config.WorkerDirs.research_data / project_name).exists():
            (config.WorkerDirs.research_data / project_name).mkdir()
        if not (config.WorkerDirs.research_data / self.project_name / 'runs').exists():
            (config.WorkerDirs.research_data / self.project_name / 'runs').mkdir(parents=True)
        self.remove_test_runs()
        self.param_nums = self.load_param_nums()

    def remove_test_runs(self):  # otherwise 'param_test' will be included in param_names
        for p in (config.WorkerDirs.research_data / self.project_name / 'runs').iterdir():
            if p.name.endswith('test'):
                shutil.rmtree(str(p))

    def load_param_nums(self):
        res = [int(p.name.split('_')[-1])
               for p in (config.WorkerDirs.research_data / self.project_name / 'runs').glob('param*')] or [0]
        return res

    @staticmethod
    def is_same(param2val1, param2val2):
        d1 = {k: v for k, v in param2val1.items() if k not in ['job_name', 'param_name']}
        d2 = {k: v for k, v in param2val2.items() if k not in ['job_name', 'param_name']}
        return d1 == d2

    def get_param_name(self,
                       param2val1: Dict[str, Any],
                       runs_path: Optional[Path] = None,
                       ) -> Tuple[str, str]:
        """
        check if param2val exists in runs.
        only if it doesn't exist, create a new one (otherwise problems with queued runs might occur)
        """
        # check runs
        if runs_path is None:
            runs_path = config.WorkerDirs.research_data / self.project_name / 'runs'

        for param_p in runs_path.glob('param_*'):
            with (param_p / 'param2val.yaml').open('r') as f:
                param2val2 = yaml.load(f, Loader=yaml.FullLoader)
            if self.is_same(param2val1, param2val2):
                return 'old', param_p.name
        else:
            new_param_num = max(self.param_nums) + 1
            self.param_nums.append(new_param_num)
            param_name = 'param_{}'.format(new_param_num)
            return 'new', param_name

    def count_num_times_logged(self,
                               param_name: str,
                               runs_path: Optional[Path] = None
                               ) -> int:
        if runs_path is None:
            runs_path = config.WorkerDirs.research_data / self.project_name / 'runs'

        res = len(list((runs_path / param_name).glob('*num*')))
        return res