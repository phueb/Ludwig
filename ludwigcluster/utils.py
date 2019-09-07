import numpy as np
from itertools import cycle
import yaml


def _iter_over_cycles(param2opts):
    """
    return list of mappings from param name to integer which is index to possible param values
    all possible combinations are returned
    """
    lengths = []
    for k, v in param2opts:
        lengths.append(len(v))
    total = np.prod(lengths)
    num_lengths = len(lengths)
    # cycles
    cycles = []
    prev_interval = 1
    for n in range(num_lengths):
        l = np.concatenate([[i] * prev_interval for i in range(lengths[n])])
        if n != num_lengths - 1:
            c = cycle(l)
        else:
            c = l
        cycles.append(c)
        prev_interval *= lengths[n]
    # iterate over cycles, in effect retrieving all combinations
    param_ids = []
    for n, i in enumerate(zip(*cycles)):
        param_ids.append(i)
    assert sorted(list(set(param_ids))) == sorted(param_ids)
    assert len(param_ids) == total
    return param_ids


def list_all_param2vals(param2requests, param2default, update_d=None, add_names=True):
    # complete partial request made by user
    full_request = {k: [v] if k not in param2requests else param2requests[k]
                    for k, v in param2default.copy().items()}
    #
    param2opts = tuple(full_request.items())
    param_ids = _iter_over_cycles(param2opts)
    # map param names to integers corresponding to which param value to use
    res = []
    for ids in param_ids:
        param2val = {k: v[i] for (k, v), i in zip(param2opts, ids)}
        if add_names:
            param2val.update({'param_name': None, 'job_name': None})
        if isinstance(update_d, dict):
            param2val.update(update_d)
        res.append(param2val)
    return res


def gen_param_ps(partial_request, default_params, runs_p, label_params=None):
    """
    Return path objects that point to folders with job results.
     Folders located in those paths are each generated with the same parameter configuration.
     Use this for retrieving data after a job has been completed
    """
    print('Requested:')
    print(partial_request)
    print()
    #
    label_params = set([param for param, val in partial_request.items()
                        if val != default_params.__dict__[param]] + (label_params or []))
    #
    requested_param2vals = list_all_param2vals(partial_request, default_params, add_names=False)
    for param_p_ in runs_p:
        print('Checking {}...'.format(param_p_))
        # load param2val
        with (param_p_ / 'param2val.yaml').open('r') as f:
            param2val = yaml.load(f, Loader=yaml.FullLoader)
        param2val = param2val.copy()
        param2val['param_name'] = 'default'
        param2val['job_name'] = 'default'
        # is match?
        if param2val in requested_param2vals:
            label_ = '\n'.join(['{}={}'.format(param, param2val[param]) for param in label_params])
            label_ += '\nn={}'.format(len(list(param_p_.glob('*num*'))))
            print('Param2val matches')
            print(label_)
            yield param_p_, label_
        else:
            print('Params do not match')