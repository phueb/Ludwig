import pandas as pd


def prepare_data():
    print('Preparing data + Saving data to file server...')


def main(param2val):

    # e.g. train a neural network
    lr = param2val['learning_rate']
    print('Training neural network with learning_rate={}'.format(lr), flush=True)
    precision = [0.5, 0.5, 0.8]
    recall = [0.4, 0.6, 0.7]

    # convert performance measure to pandas
    s1 = pd.Series(precision, index=[1, 2, 3])
    s1.name = 'precision'

    s2 = pd.Series(recall, index=[1, 2, 3])
    s2.name = 'recall'

    return [s1, s2]  # must return a list of pandas Series

