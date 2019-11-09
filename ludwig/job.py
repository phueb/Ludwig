from pathlib import Path
import datetime
import yaml
from typing import List, Dict, Optional, Any, Tuple

from ludwig import config
from ludwig import print_ludwig


class Job:
    """
    handle and update the parameter configuration which defines a job
    """

    def __init__(self,
                 param2val: Dict[str, Any],
                 ):
        self.param2val = param2val
        self.is_new = None

    @staticmethod
    def is_same(param2val1, param2val2):
        d1 = {k: v for k, v in param2val1.items() if k not in config.Constants.added_param_names}
        d2 = {k: v for k, v in param2val2.items() if k not in config.Constants.added_param_names}
        return d1 == d2

    def update_param_name(self,
                          runs_path: Path,
                          num_new: int,  # number of new param_names assigned
                          ) -> None:
        """
        check if param2val exists in runs.
        only if it doesn't exist, create a new one (otherwise problems with queued runs might occur)
        """
        param_nums = [int(p.name.split('_')[-1])
                      for p in runs_path.glob('param*')
                      if config.Constants.not_ludwig not in p.name] or [0]

        for param_p in runs_path.glob('param_*'):
            with (param_p / 'param2val.yaml').open('r') as f:
                loaded_param2val = yaml.load(f, Loader=yaml.FullLoader)
            if self.is_same(self.param2val, loaded_param2val):
                print_ludwig('Configuration matches existing configuration')
                self.is_new = False
                param_name = param_p.name
                break
        else:
            new_param_num = max(param_nums) + 1 + num_new
            param_nums.append(new_param_num)
            param_name = 'param_{}'.format(new_param_num)
            self.is_new = True

        self.param2val['param_name'] = param_name
        print_ludwig(f'Assigned param_name={param_name: <12} to job')

    def calc_num_needed(self,
                        runs_path: Path,
                        reps: int,
                        disable: bool = False,  # for unit-testing or debugging
                        ):
        param_name = self.param2val['param_name']
        num_times_logged = len(list((runs_path / param_name).glob('*num*')))
        num_times_logged = num_times_logged if not disable else 0
        res = reps - num_times_logged
        res = max(0, res)
        print_ludwig('{:<10} logged {:>3} times. Will execute job {:>3} times'.format(
            param_name, num_times_logged, res))
        return res

    def update_job_name(self,
                        rep_id: int,
                        ) -> None:

        # add job_name
        time_of_init = datetime.datetime.now().strftime(config.Time.format)
        job_name = '{}_num{}'.format(time_of_init, rep_id)
        self.param2val['job_name'] = job_name

        # add save_path - must not be on shared drive because contents are copied to shred drive at end of job
        save_path = Path(self.param2val['param_name']) / job_name / config.Constants.saves
        self.param2val['save_path'] = str(save_path)

    def is_ready(self) -> bool:
        for name in config.Constants.added_param_names:
            if name not in self.param2val:
                return False
        else:
            return True

    def __repr__(self):
        res = ''
        for k, v in self.param2val.items():
            res += f'{k:<16} {v}\n'
        return res.strip('\n')