import datetime
from termcolor import cprint
import socket
import csv

from ludwigcluster import config


class Starter:
    """
    Contains methods for reading params from disk, checking, and supplying params for NN training.
    """

    def __init__(self,
                 project_name,
                 default_params,
                 check_fn,
                 log_entry_dicts):
        self.project_name = project_name
        self.default_params = default_params
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

    def make_checked_params_list(self, new_params_list):
        res = []
        new_param_names = set()
        for new_params in new_params_list:
            params = self.default_params.copy()
            # overwrite
            for config_name, config_value in new_params.items():
                if config_name not in self.default_params.keys():
                    raise Exception('"{}" is not a valid config.'.format(config_name))
                else:
                    params[config_name] = self.to_correct_type(config_value)
                    new_param_names.add(config_name)
            # check + add
            self.check_fn(params, new_param_names)
            res.append(params)
        return res

    def load_new_params_list(self):
        p = config.Dirs.lab / self.project_name / 'new_params.csv'
        if not p.exists():
            print('Did not find {}'.format(p))
        res = list(csv.DictReader(p.open('r')))
        print('New Params:')
        for n, d in enumerate(res):
            print('Params {}:'.format(n))
            for k, v in sorted(d.items()):
                print('{:>20} -> {:<20}'.format(k, v))
        return res

    def gen_params(self, reps):
        # load + parse + check
        new_params_list = self.load_new_params_list()
        checked_params_list = self.make_checked_params_list(new_params_list)
        # generate
        for n, params in enumerate(checked_params_list):
            cprint('==================================', 'blue')
            # make num_times_train
            num_times_logged = 0
            num_times_logged += self.count_num_times_logged(params)
            num_times_train = reps - num_times_logged
            cprint('Config {} logged {} times'.format(n, num_times_logged), 'blue')
            # generate
            num_times_train = max(0, num_times_train)
            color = 'green' if num_times_train > 0 else 'blue'
            cprint('Will train Config {} {} times'.format(n, num_times_train), color)
            cprint('==================================', 'blue')
            if num_times_train > 0:
                for _ in range(num_times_train):
                    # timestamp
                    params.model_name = self.make_model_name(params.flavor)
                    yield params

    def count_num_times_logged(self, params):
        num_times_logged = 0
        if not self.log_entry_dicts:
            return 0
        # make num_times_logged
        for log_entry_d in self.log_entry_dicts:
            bool_list = []
            for name, value in params.items():  # TODO test - need .dict.items()?
                if name == 'model_name':
                    continue
                try:
                    bool_list.append(value == log_entry_d[name])
                except KeyError:
                    print('WARNING: config {} not found in main log'.format(name))
                    pass
            if all(bool_list):
                num_times_logged += 1
        return num_times_logged
