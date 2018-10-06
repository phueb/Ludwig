import pandas as pd
import csv
import shutil
from itertools import chain

from src import config


class Logger:
    """
    Methods for interacting with log
    """

    def __init__(self, default_configs_dict):
        self.default_configs_dict = default_configs_dict
        self.log_path = config.Dirs.log / 'log.csv'

    # //////////////////////////////////////////////////////////////// log file

    @staticmethod
    def delete_model(model_name):
        path = config.Dirs.runs / model_name
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
        for model_name in config.Dirs.runs.glob('*_*'):
            info_file_path = config.Dirs.backup_runs / model_name / 'Configs' / 'info.csv'
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
        info_file_path = config.Dirs.runs / log_entry_d['model_name'] / 'Configs' / 'info.csv'
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

    @property
    def manipulated_config_names(self):
        """
        Returns list of all config_names for which there is more than one unique value in all logs
        """
        result = []
        for config_name in self.all_config_names:
            config_values = self.get_config_values_from_log(config_name, req_completion=False)
            is_manipulated = True if len(list(set(config_values))) > 1 else False
            if is_manipulated and config_name in self.all_config_names:
                result.append(config_name)
        # if empty
        if not result:
            result = ['flavor']
        return result

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

    def make_log_dicts(self, config_names):
        log_entry_dicts = self.load_log()
        # df
        column_names = ['model_name'] + config_names + ['timepoint']
        column_names += ['num_saves'] if 'num_saves' not in config_names else []
        df = pd.DataFrame(data={column_name: [d[column_name] for d in log_entry_dicts]
                                for column_name in column_names})[column_names]
        # make log_dicts
        log_dicts = []
        for config_values, group_df in df.groupby(config_names):
            if not isinstance(config_values, tuple):
                config_values = [config_values]
            model_names = group_df['model_name'].tolist()
            log_dict = {'model_names': model_names,
                        'flavor': model_names[0].split('_')[1],
                        'model_desc': '\n'.join('{}={}'.format(config_name, config_value)
                                                for config_name, config_value in zip(config_names, config_values)),
                        'data_rows': [row.tolist() for ow_id, row in group_df.iterrows()]}
            log_dicts.append(log_dict)
        results = log_dicts[::-1]
        return results

    @staticmethod
    def make_log_df(summary_flavors, summary_hostnames):
        log_file_paths = [config.Dirs.log / f.name for f in config.Dirs.log.glob('log*.*')
                          if f.stem.split('_')[-1] in summary_hostnames]
        if not log_file_paths:
            result = pd.DataFrame()  # in case no matching log files found
        else:
            result = pd.DataFrame(pd.concat((pd.read_csv(f) for f in log_file_paths)))
            if not result.empty:
                result['flavor'] = result['model_name'].apply(lambda model_name: model_name.split('_')[1])
                result = result[result['timepoint'] == result['num_saves']]
                result = result[result['flavor'].isin(summary_flavors)]
        return result

    def concat_info_files(self, verbose=False):
        # make log_file_paths
        info_file_paths = [config.Dirs.backup_runs / model_name / 'Configs' / 'info.csv'
                           for model_name in config.Dirs.backup_runs.glob('*_*')
                           if (config.Dirs.backup_runs / model_name / 'Configs' / 'info.csv').exists()]
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

    def get_timepoints(self, model_name):
        last_timepoint = [d['timepoint'] for d in self.load_log()
                          if d['model_name'] == model_name][0]
        result = list(range(last_timepoint + 1))
        return result

    def make_common_timepoint(self, model_names_list, common_timepoint=config.Interface.common_timepoint):
        timepoints_list_list = []
        for model_names in model_names_list:
            timepoints_list = [self.get_timepoints(model_name) for model_name in model_names]
            timepoints_list_list.append(timepoints_list)
        sets = [set(list(chain(*l))) for l in timepoints_list_list]
        # default
        if common_timepoint is not None and common_timepoint in set.intersection(*sets):
            print('Using default common timepoint: {}'.format(common_timepoint))
            return common_timepoint
        else:
            print('Did not find default common timepoint.')
        # common
        result = max(set.intersection(*sets))
        print('Found last common timepoint: {}'.format(result))
        return result
