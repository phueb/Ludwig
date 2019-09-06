import numpy as np
from itertools import cycle


def iter_over_cycles(d):
    # lengths
    param2opts = sorted([(k, v) for k, v in d.items()
                         if not k.startswith('_')])
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
    return param2opts, param_ids


def list_all_param2vals(params, update_d=None, add_names=True):
    """
    return list of mappings from param name to integer which is index to possible param values
    all possible combinations are returned
    """
    d = params_class.__dict__
    #
    param2opts, param_ids = iter_over_cycles(d)
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