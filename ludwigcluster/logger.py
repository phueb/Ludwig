import shutil
import datetime
import re
import yaml
from shutil import copyfile

from ludwigcluster import config


class Logger:
    """
    Methods for interacting with log
    """

    def __init__(self, project_name):
        self.project_name = project_name
        if not (config.Dirs.lab / self.project_name).exists():
            (config.Dirs.lab / self.project_name / 'runs').mkdir(parents=True)
            (config.Dirs.lab / self.project_name / 'backup').mkdir()

    def delete_model(self, job_name):
        path = config.Dirs.lab / self.project_name / 'runs' / job_name
        try:
            shutil.rmtree(str(path))
        except OSError:  # sometimes only log entry is created, and no model files
            print('WARNING: Error deleting {}'.format(path))
        else:
            print('Deleted {}'.format(job_name))

    def delete_incomplete_models(self):
        delta = datetime.timedelta(hours=config.Time.delete_delta)
        time_of_init_cutoff = datetime.datetime.now() - delta
        for p in (config.Dirs.lab / self.project_name / 'runs').glob('*_*'):
            if not (config.Dirs.lab / self.project_name / 'backup' / p.name).exists():
                result = re.search('_(.*)_', p.name)
                time_of_init = result.group(1)
                dt = datetime.datetime.strptime(time_of_init, config.Time.format)
                if dt < time_of_init_cutoff:
                    print('Found dir more than {} hours old that is not backed-up.'.format(
                        config.Time.delete_delta))
                    self.delete_model(p)

    def load_log(self, which):  # TODO implement
        if which == 'runs':
            print('Loading runs log')
        elif which == 'backup':
            print('Loading backup log')
        else:
            raise AttributeError('Invalid arg to "which" (log).')
        raise NotImplemented('what is best way to represent log?')

    def count_num_times_in_backup(self, param2val1):  # TODO test
        num_times_logged = 0
        for p in (config.Dirs.lab / self.project_name / 'backup').rglob('*.yaml'):
            with p.open('r') as f:
                param2val2 = yaml.load(f)
            if param2val1 == param2val2:
                num_times_logged += 1
        return num_times_logged


    def backup(self, job_name):  # TODO test
        """
        this informs LudwigCluster that training has completed (backup is only called after training completion)
        copies all data created during training to backup_dir.
        Uses custom copytree fxn to avoid permission errors when updating permissions with shutil.copytree.
        Copying permissions can be problematic on smb/cifs type backup drive.
        """
        src = config.Dirs.lab / self.project_name / 'runs' / job_name
        dst = config.Dirs.lab / self.project_name / 'backup' / job_name

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
        print('Backing up data...')
        try:
            copytree(src, dst)
        except PermissionError:
            print('LudwigCluster: Backup failed. Permission denied.')
        except FileExistsError:
            print('LudwigCluster: Already backed up')
        else:
            print('Backed up data to {}'.format(dst))