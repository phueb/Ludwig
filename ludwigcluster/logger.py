import pandas as pd
import csv
import shutil

from ludwigcluster import config


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

    def delete_incomplete_models(self):
        for model_name in (config.Dirs.lab / self.project_name).glob('*_*'):
            info_file_path = config.Dirs.lab / self.project_name / model_name / 'Configs' / 'info.csv'
            with info_file_path.open('r') as f:
                reader = csv.DictReader(f)
                log_entry_d = next(reader)  # TODO test
                if log_entry_d['num_saves'] != log_entry_d['timepoint']:
                    model_name = log_entry_d['model_name']
                    self.delete_model(model_name)

    def load_log(self):
        self.concat_info_files()  # TODO test
        with self.log_path.open('r') as f:
            reader = csv.DictReader(f)
            result = []
            for log_entry_d in reader:
                result.append(self.to_correct_types(log_entry_d))
        return result

    def write_info_file(self, configs_dict, timepoint):
        log_entry_d = configs_dict.copy()
        log_entry_d['timepoint'] = timepoint
        info_file_path = config.Dirs.lab / self.project_name / log_entry_d['model_name'] / 'Configs' / 'info.csv'
        with info_file_path.open('w') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerow(self.to_strings(log_entry_d))

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
        fieldnames.append('timepoint')
        return fieldnames

    @property
    def all_config_names(self):
        all_config_names = sorted(self.default_configs_dict.keys())
        return all_config_names

    def get_config_values_from_log(self, config_name, req_completion=True):
        values = set()
        log_entry_dicts = self.load_log()
        for log_entry_d in log_entry_dicts:
            if req_completion:
                if log_entry_d['timepoint'] == log_entry_d['num_saves']:
                    try:
                        config_value = log_entry_d[config_name]
                    except KeyError:  # sometimes new config names are added
                        print('rnnlab WARNING: Did not find "{}" in main log.'.format(config_name))
                        continue
                    values.add(config_value)
            else:
                values.add(log_entry_d[config_name])
        result = list(values)
        return result

    def concat_info_files(self, verbose=False):
        # make info_file_paths
        info_file_paths = [config.Dirs.lab / self.project_name / model_name / 'Configs' / 'info.csv'
                           for model_name in (config.Dirs.lab / self.project_name).glob('*_*')
                           if (config.Dirs.lab / self.project_name / model_name / 'Configs' / 'info.csv').exists()]
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