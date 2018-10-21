import csv
import datetime
from termcolor import cprint
import socket

from ludwigcluster import config


class Starter:
    """
    Contains methods for reading configs from disk, checking, and supplying configs for NN training.
    """

    def __init__(self,
                 reps,
                 default_configs_dict,
                 check_fn,
                 log_entry_dicts):
        self.reps = reps
        self.default_configs_dict = default_configs_dict
        self.check_fn = check_fn
        self.log_entry_dicts = log_entry_dicts

    @staticmethod
    def to_flavor(model_name):
        flavor = model_name.split('_')[1]
        return flavor

    @staticmethod
    def make_model_name(flavor):
        time_of_init = datetime.datetime.now().strftime('%m-%d-%H-%M-%S')
        hostname = socket.gethostname()
        model_name = '{}_{}_{}'.format(hostname, time_of_init, flavor)
        return model_name

    @staticmethod
    def to_correct_type(value):
        if value.isdigit():
            value = int(value)
        elif value == 'None':
            value = None
        elif '.' in value:
            value = float(value)
        else:
            value = str(value)
        return value


    def make_checked_configs_dicts(self, new_configs_dicts):
        configs_dicts = []
        new_config_names = set()
        for new_configs_dict in new_configs_dicts:
            configs_dict = self.default_configs_dict.copy()
            # overwrite
            for config_name, config_value in new_configs_dict.items():
                if config_name not in self.default_configs_dict.keys():
                    raise Exception('"{}" is not a valid config.'.format(config_name))
                else:
                    configs_dict[config_name] = self.to_correct_type(config_value)
                    new_config_names.add(config_name)
            # add configs_dict
            self.check_fn(configs_dict, new_config_names)
            configs_dicts.append(configs_dict)
        return configs_dicts

    def gen_configs_dicts(self, new_configs_dicts):
        # parse + check
        checked_config_dicts = self.make_checked_configs_dicts(new_configs_dicts)
        # generate
        for config_id, configs_dict in enumerate(checked_config_dicts):
            cprint('==================================', 'blue')
            # make num_times_train
            num_times_logged = 0
            num_times_logged += self.count_num_times_logged(configs_dict)
            num_times_train = self.reps - num_times_logged
            cprint('Config {} logged {} times'.format(config_id, num_times_logged), 'blue')
            # generate
            num_times_train = max(0, num_times_train)
            color = 'green' if num_times_train > 0 else 'blue'
            cprint('Will train Config {} {} times'.format(config_id, num_times_train), color)
            cprint('==================================', 'blue')
            if num_times_train > 0:
                for _ in range(num_times_train):
                    # timestamp
                    configs_dict['model_name'] = self.make_model_name(configs_dict['flavor'])
                    yield configs_dict

    def count_num_times_logged(self, configs_dict):
        num_times_logged = 0
        if not self.log_entry_dicts:
            return 0
        # make num_times_logged
        for log_entry_d in self.log_entry_dicts:
            bool_list = []
            for config_name, config_value in configs_dict.items():
                if config_name == 'model_name':
                    continue
                try:
                    bool_list.append(config_value == log_entry_d[config_name])
                except KeyError:
                    print('WARNING: config {} not found in main log'.format(config_name))
                    pass
            if all(bool_list):
                num_times_logged += 1
        return num_times_logged
