import shutil
import datetime
import re
import yaml
import sys
from shutil import copyfile

from ludwigcluster import config


class Logger:
    """
    in-memory log for keeping track of which jobs have completed (and which have the same param2vals)
    """

    def __init__(self, project_name, delete_delta):
        self.project_name = project_name
        self.delete_delta = delete_delta
        self.param_nums = [int(p.name.split('_')[-1]) for p in (config.Dirs.lab / project_name / 'backup').iterdir()]
        print('Initialized logger with project_name={}'.format(project_name))
        if not (config.Dirs.lab / self.project_name / 'runs').exists():
            print('Making runs dir')
            (config.Dirs.lab / self.project_name / 'runs').mkdir(parents=True)
        if not (config.Dirs.lab / self.project_name / 'backup').exists():
            print('Making backup dir')
            (config.Dirs.lab / self.project_name / 'backup').mkdir(parents=True)

    def delete_model(self, job_name):
        path = config.Dirs.lab / self.project_name / 'runs' / job_name
        try:
            shutil.rmtree(str(path))
        except OSError:  # sometimes only log entry is created, and no model files
            print('WARNING: Error deleting {}'.format(path))
        else:
            print('Deleted {}'.format(job_name))

    def delete_incomplete_models(self):
        delta = datetime.timedelta(hours=self.delete_delta)
        time_of_init_cutoff = datetime.datetime.now() - delta
        for p in (config.Dirs.lab / self.project_name / 'runs').glob('**/*num*'):
            if not (config.Dirs.lab / self.project_name / 'backup' / p.parent.name / p.name).exists():
                result = re.search('_(.*)_', p.name)
                time_of_init = result.group(1)
                dt = datetime.datetime.strptime(time_of_init, config.Time.format)
                if dt < time_of_init_cutoff:
                    print('Found dir more than {} hours old that is not backed-up.'.format(self.delete_delta))
                    self.delete_model(p)

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
        for param_p in (config.Dirs.lab / self.project_name / 'backup').iterdir():
            with (param_p / 'param2val.yaml').open('r') as f:
                param2val2 = yaml.load(f)
            if self.is_same(param2val1, param2val2):
                return param_p.name
        else:
            new_param_num = max(self.param_nums) + 1
            self.param_nums.append(new_param_num)
            param_name = 'param_{}'.format(new_param_num)
            return param_name

    def count_num_times_in_backup(self, param_name):  # TODO count until param folder is ofund that has matchign param2val
        res = len(list((config.Dirs.lab / self.project_name / 'backup' / param_name).glob('*num*')))
        return res

    def backup(self, param_name, job_name):
        """
        this informs LudwigCluster that training has completed (backup is only called after training completion)
        copies all data created during training to backup_dir.
        Uses custom copytree fxn to avoid permission errors when updating permissions with shutil.copytree.
        Copying permissions can be problematic on smb/cifs type backup drive.
        """
        src = config.Dirs.lab / self.project_name / 'runs' / param_name / job_name
        dst = config.Dirs.lab / self.project_name / 'backup' / param_name / job_name

        def copytree(s, d):
            d.mkdir()
            for i in s.iterdir():
                s_i = s / i.name
                d_i = d / i.name
                if s_i.is_dir():
                    copytree(s_i, d_i)

                else:
                    copyfile(str(s_i), str(d_i))  # copyfile works because it doesn't update any permissions
        # copy
        print('Backing up data...  DO NOT INTERRUPT!')
        try:
            copytree(src, dst)
        except PermissionError:
            print('LudwigCluster: Backup failed. Permission denied.')
        except FileExistsError:
            print('LudwigCluster: Already backed up')
        else:
            print('Backed up data to {}'.format(dst))