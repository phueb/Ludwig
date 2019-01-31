import yaml

from ludwigcluster import config


class Logger:
    """
    in-memory log for keeping track of which jobs have completed (and which have the same param2vals)
    """

    def __init__(self, project_name):
        self.project_name = project_name
        if not (config.Dirs.lab / project_name).exists():
            (config.Dirs.lab / project_name).mkdir()
        print('Initialized logger with project_name={}'.format(project_name))
        if not (config.Dirs.lab / self.project_name / 'runs').exists():
            print('Making runs dir')
            (config.Dirs.lab / self.project_name / 'runs').mkdir(parents=True)
        if not (config.Dirs.lab / self.project_name / 'backup').exists():
            print('Making backup dir')
            (config.Dirs.lab / self.project_name / 'backup').mkdir(parents=True)
        self.param_nums = [int(p.name.split('_')[-1])
                           for p in (config.Dirs.lab / project_name / 'backup').iterdir()] or [0]

    @staticmethod
    def is_same(param2val1, param2val2):
        d1 = {k: v for k, v in param2val1.items() if k not in ['job_name', 'param_name']}
        d2 = {k: v for k, v in param2val2.items() if k not in ['job_name', 'param_name']}
        return d1 == d2

    def get_param_name(self, param2val1):
        """
        check if param2val exists in backup, and if not, check if it exists in runs.
        only if it doesn't exist, create a new one (otherwise problems with queued runs might occur)
        """
        # check backup
        for param_p in (config.Dirs.lab / self.project_name / 'backup').glob('param_*'):
            with (param_p / 'param2val.yaml').open('r') as f:
                param2val2 = yaml.load(f)
            if self.is_same(param2val1, param2val2):
                return param_p.name
        # check runs
        for param_p in (config.Dirs.lab / self.project_name / 'runs').glob('param_*'):
            with (param_p / 'param2val.yaml').open('r') as f:
                param2val2 = yaml.load(f)
            if self.is_same(param2val1, param2val2):
                return param_p.name
        else:
            new_param_num = max(self.param_nums) + 1
            self.param_nums.append(new_param_num)
            param_name = 'param_{}'.format(new_param_num)
            return param_name

    def count_num_times_in_backup(self, param_name):
        res = len(list((config.Dirs.lab / self.project_name / 'backup' / param_name).glob('*num*')))
        return res