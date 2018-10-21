import pandas as pd
import shutil

from ludwigcluster import config


# TODO timepoint is depreciated - model is assumed complete if data has been backed-up


class Logger:
    """
    Methods for interacting with log
    """

    def __init__(self, project_name):
        self.project_name = project_name
        self.log_path = config.Dirs.lab / project_name / 'log.csv'

    # //////////////////////////////////////////////////////////////// log file

    def delete_model(self, model_name):
        path = config.Dirs.lab / self.project_name / model_name
        try:
            shutil.rmtree(str(path))
        except OSError:  # sometimes only log entry is created, and no model files
            print('rnnlab WARNING: Could not delete {}'.format(path))
        else:
            print('Deleted {}'.format(model_name))

    def delete_incomplete_models(self):  # TODO test - delete models which don't have folder in backup dir
        for model_name in (config.Dirs.lab / self.project_name).glob('*_*'):
            if not (config.Dirs.lab / self.project_name / model_name).exits():
                self.delete_model(model_name)

    def load_log(self):  # TODO test - log is not saved but stored in memory
        print('Loading log')
        ps = []
        for model_name in (config.Dirs.lab / self.project_name / 'runs').glob('*_*'):

            print(model_name)
            raise SystemExit

            if (config.Dirs.lab / self.project_name / model_name / 'params.csv').exists():
                p = config.Dirs.lab / self.project_name / model_name / 'params.csv'
                ps.append(p)

        # concatenate
        if not ps:
            print('Did not find individual info files to concatenate into log file.\n'
                  'Creating empty log file.')
            res = pd.DataFrame()
        else:
            res = pd.DataFrame(pd.concat((pd.read_csv(f, index_col=0)
                                          for f in ps)))


        # TODO remove
        res = pd.read_csv('/home/ph/mock_log.csv')


        return res

    def write_param_file(self, params):  # TODO replace with pandas
        """
        writes csv file to shared directory on LudwigCluster
        this is required for logger - builds log from param files
        """
        p = config.Dirs.lab / self.project_name / params.model_name / 'params.csv'
        if not p.parent.exits():
            p.mkdir(parents=True)

        raise NotImplementedError
        # TODO insert model_name in first column