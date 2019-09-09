import sys
import pandas as pd


def prepare_data():
    print('Preparing data + Saving data to file server...')


def main(param2val):

    # e.g. train a neural network
    lr = param2val['learning_rate']
    print('Training neural network with learning_rate={}'.format(lr))
    sys.stdout.flush()

    # must return a list of pandas dataframes and each must be given a name attribute
    df1 = pd.DataFrame(data={'col1': [1, 2, 3], 'col2': [6, 7, 8]})
    df2 = pd.DataFrame()
    df1.name = 'df1'
    df2.name = 'df2'

    return df1, df2

