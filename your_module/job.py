
from your_module import config


def pre_processing_job():
    print('Preprocessing + Saving data to file server...')


def main(param2val):
    # check if host is down - do this before any computation
    results_p = config.RemoteDirs.runs / param2val['param_name'] / param2val['job_name'] / 'results.csv'
    assert config.RemoteDirs.runs.exists()  # this throws error if host is down

    print('Training neural network...')

