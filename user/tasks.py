import torch


def main(**kwargs):

    print('keyword-args:')
    for k, v in kwargs.items():
        print(k, v)

    print('CUDA is available:')
    print(torch.cuda.is_available())

    print('GPU 0 name:')
    print(torch.cuda.get_device_name(0))