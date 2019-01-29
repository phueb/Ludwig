import shutil
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
        self.param_nums = [int(p.name.split('_')[-1]) for p in (config.Dirs.lab / project_name / 'backup').iterdir()]

    @staticmethod
    def delete_param_dir(params_p):
        shutil.rmtree(str(params_p))
        print('Deleted {}'.format(params_p))

    def delete_param_dirs_not_in_backup(self):
        """
        this is necessary to do before submission, because param2val_list is shuffled,
        and this could result in a param2val that has not yet been assigned a param_name (in backup_dir) to be
        assigned a different param_num across submissions
        """
        for params_p in (config.Dirs.lab / self.project_name / 'runs').glob('param_*'):
            if not (config.Dirs.lab / self.project_name / 'backup' / params_p.name).exists():
                    self.delete_param_dir(params_p)

    def load_log(self, which):  # TODO implement
        if which == 'runs':
            print('Loading runs log')
        elif which == 'backup':
            print('Loading backup log')
        else:
            raise AttributeError('Invalid arg to "which" (log).')
        raise NotImplemented('what is best way to represent log?')

    @staticmethod
    def is_same(param2val1, param2val2):
        d1 = {k: v for k, v in param2val1.items() if k not in ['job_name', 'param_name']}
        d2 = {k: v for k, v in param2val2.items() if k not in ['job_name', 'param_name']}
        return d1 == d2

    def get_param_name(self, param2val1):
        for param_p in (config.Dirs.lab / self.project_name / 'backup').glob('param_*'):
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