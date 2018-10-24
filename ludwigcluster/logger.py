import pandas as pd
import shutil
import datetime
import re

from ludwigcluster import config


class Logger:
    """
    Methods for interacting with log
    """

    def __init__(self, project_name):
        self.project_name = project_name
        self.log_path = config.Dirs.lab / project_name / 'log.csv'
        if not (config.Dirs.lab / self.project_name).exists():
            (config.Dirs.lab / self.project_name / 'runs').mkdir(parents=True)
            (config.Dirs.lab / self.project_name / 'backup').mkdir()

    def delete_model(self, model_name):
        path = config.Dirs.lab / self.project_name / model_name
        try:
            shutil.rmtree(str(path))
        except OSError:  # sometimes only log entry is created, and no model files
            print('WARNING: Error deleting {}'.format(path))
        else:
            print('Deleted {}'.format(model_name))

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
                    print(p.name)
                self.delete_model(p)

    def load_log(self, which):
        if which == 'runs':
            print('Loading runs log')
        elif which == 'backup':
            print('Loading backup log')
        else:
            raise AttributeError('Invalid arg to "which" (log).')
        params_file_paths = [p for p in (config.Dirs.lab / self.project_name / which).rglob('params.csv')]
        # concatenate
        if not params_file_paths:
            print('Did not find any data in {} from which to build log.\n'
                  'Creating empty log file.'.format(config.Dirs.lab / self.project_name / 'runs'))
            res = pd.DataFrame()
        else:
            res = pd.DataFrame(pd.concat((pd.read_csv(f, index_col=False) for f in params_file_paths)))
        return res

    def count_num_times_in_backup(self, params_df_row):
        num_times_logged = 0
        for n, log_df_row in self.load_log('backup').iterrows():
            if all([params_df_row[k] == log_df_row[k] for k in params_df_row.index]):
                num_times_logged += 1
        return num_times_logged

    def save_params_df_row(self, params_df_row):
        """
        writes csv file to shared directory on LudwigCluster
        this is required for logger - builds log from param files
        """
        p = config.Dirs.lab / self.project_name / 'runs' / params_df_row['model_name'].values[0] / 'params.csv'
        if not p.parent.exists():
            p.parent.mkdir(parents=True)
        params_df_row.to_csv(p, index=False)