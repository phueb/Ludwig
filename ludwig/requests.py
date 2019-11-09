from itertools import cycle
from typing import Tuple, Any, Dict, List
import numpy as np


def _iter_over_cycles(param2opts: Tuple[Any, ...],
                      ):
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


def gen_all_param2vals(param2requests: Dict[str, list],
                       param2default: Dict[str, Any],
                       ) -> List[Dict[str, Any]]:
    """
    return multiple param2val objects,
     each defining the parameter configuration for a singel job
    """

    # check that requests are lists
    for k, v in param2requests.items():
        if not isinstance(v, list):
            raise ValueError('Ludwig: Values in param2requests must be of type list.')

    # complete partial request made by user
    full_request = {k: [v] if k not in param2requests else param2requests[k]
                    for k, v in param2default.items()}
    #
    param2opts = tuple(full_request.items())
    param_ids = _iter_over_cycles(param2opts)

    for ids in param_ids:
        # map param names to integers corresponding to which param value to use
        param2val = {k: v[i] for (k, v), i in zip(param2opts, ids)}
        yield param2val