import torch


def deep_learning_task(**kwargs):

    print('keyword-args:')
    for k, v in kwargs.items():
        print(k, v)

    print('cuda is available:')
    print(torch.cuda.is_available())