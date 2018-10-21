import pandas as pd
import csv
import shutil

from ludwigcluster import config


# TODO timepoint is depreciated - model is assumed complete if data has been backed-up


class Logger:
    """
    Methods for interacting with log
    """

    def __init__(self, project_name, default_configs_dict):
        self.project_name = project_name
        self.default_configs_dict = default_configs_dict
        self.log_path = config.Dirs.lab / project_name / 'log.csv'
        #
        if not self.log_path.is_file():
            print('Did not find log file in {}'.format(self.log_path))
            self.write_log()

    # //////////////////////////////////////////////////////////////// log file

    def delete_model(self, model_name):
        path = config.Dirs.lab / self.project_name / model_name
        try:
            shutil.rmtree(str(path))
        except OSError:  # sometimes only log entry is created, and no model files
            print('rnnlab WARNING: Could not delete {}'.format(path))
        else:
            print('Deleted {}'.format(model_name))

    def write_log(self):
        with self.log_path.open('w') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
        print('Created log file {}'.format(self.log_path))

    def delete_incomplete_models(self):  # TODO test - delete models which don't have folder in backup dir
        for model_name in (config.Dirs.lab / self.project_name).glob('*_*'):
            if not (config.Dirs.lab / self.project_name / model_name).exits():
                self.delete_model(model_name)

    def load_log(self):
        self.concat_info_files()  # TODO test
        with self.log_path.open('r') as f:
            reader = csv.DictReader(f)
            result = []
            for log_entry_d in reader:
                result.append(self.to_correct_types(log_entry_d))
        return result

    # //////////////////////////////////////////////////////////////// misc

    @staticmethod
    def to_correct_types(d):
        for k, v in d.items():
            if v.isdigit():
                new_v = int(v)
            elif v == 'None':
                new_v = None
            elif '.' in v:
                new_v = float(v)
            else:
                new_v = str(v)
            d[k] = new_v
        return d

    @staticmethod
    def to_strings(d):
        for k, v in d.items():
            d[k] = str(v)
        return d

    @property
    def fieldnames(self):
        fieldnames = self.all_config_names
        fieldnames.insert(0, 'model_name')
        return fieldnames

    @property
    def all_config_names(self):
        all_config_names = sorted(self.default_configs_dict.keys())
        return all_config_names

    def concat_info_files(self, verbose=False):
        # make info_file_paths
        info_file_paths = [config.Dirs.lab / self.project_name / model_name / 'Params' / 'info.csv'
                           for model_name in (config.Dirs.lab / self.project_name).glob('*_*')
                           if (config.Dirs.lab / self.project_name / model_name / 'Params' / 'info.csv').exists()]
        # concatenate
        if not info_file_paths:
            if verbose:
                print('Did not find individual info files to concatenate into log file.\n'
                      'Creating empty log file.')
            result = pd.DataFrame()
        else:
            result = pd.DataFrame(pd.concat((pd.read_csv(f, index_col=0)
                                             for f in info_file_paths)))
        # save
        result.to_csv(self.log_path)
        return result