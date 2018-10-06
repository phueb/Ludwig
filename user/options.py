from termcolor import cprint

config_options = [('num_parts', 256, [[1, 2, 4, 8, 256, 512, 1024]]),
                  ('corpus_name', 'childes-20180319', [['childes-20171212', 'childes-20171213',
                                                        'childes-20180120', 'childes-20180315',
                                                        'childes-20180319']]),
                  ('sem_probes_name', 'semantic-raw', [['semantic-reduced',
                                                        'semantic-lemma',
                                                        'semantic-raw',
                                                        'semantic-early',
                                                        'semantic-late']]),
                  ('syn_probes_name', 'syntactic-mcdi', [['syntactic-mcdi',
                                                          'syntactic-mcdi',
                                                          'syntactic-mcdi']]),
                  ('num_types', 4096, [[32768, 16384, 8192, 4096, 2048, 1024]]),
                  ('p_noise', 'no_0', [['late', 'early', 'all', 'no'],
                                       [0, 1, 2, 3, 4, 5, 6]]),  # periodic noise
                  ('f_noise', 0, [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]),
                  ('block_order', 'inc_age', [['inc', 'dec', 'shuffled', 'unordered', 'middec', 'midinc'],
                                              ['age', 'punctuation', 'noun', 'pronoun', 'determiner', 'interjection',
                                               'preposition', '3-gram', '1-gram', 'entropy',
                                               'dec_noun+punctuation',
                                               'inc_noun+punctuation',
                                               'nouns-context-entropy-1-left',
                                               'punctuations-context-entropy-1-left',
                                               'probes-context-entropy-1-left',
                                               'conjunctions-context-entropy-1-right',
                                               'prepositions-context-entropy-1-right',
                                               'verbs-context-entropy-1-right']]),
                  ('num_iterations', 20, [[1, 2, 3, 4, 5, 10, 20]]),
                  ('syn2sem', 'dist_least_hard', [['freq', 'dist'],
                                                  ['least', 'all', 'most', 'l2m', 'm2l'],
                                                  ['soft', 'hard', 's2h', 'h2s']]),
                  ('reinit', 'none_10_w', [['none', 'mid', 'all'],
                                           [10, 50, 60, 60, 80, 90, 100],
                                           ['w', 'a', 'w+a', 'b', 'w+b']]),  # w=weights, a=adagradm b=bias
                  ('num_y', 1, [[1, 4]]),
                  ('num_saves', 10, [[1, 5, 10, 20]]),
                  ('sem-cat_task', 'none_1200', [['all', 'end', 'none'],
                                                 [100, 300, 900, 1200]]),
                  ('cat_task_lr', 0.01, [[0.01, 0.001]]),
                  ('synonym_task', 'none_1200', [['all', 'end', 'none'],
                                                 [100, 300, 900, 1200]]),
                  ('syn_task_lr', 0.01, [[0.01, 0.001]]),
                  ('match_task', 'none_1200', [['all', 'end', 'none'],
                                               [100, 300, 900, 1200]]),
                  ('match_task_lr', 0.01, [[0.01, 0.001]]),
                  ('bptt_steps', 7, [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]]),
                  ('num_layers', 1, [[1, 2, 3, 4]]),
                  ('task_layer_id', 1, [[0, 1, 2, 3]]),
                  ('rep_layer_id', 0, [[0, 1, 2, 3]]),
                  ('mb_size', 64, [[1, 2, 4, 8, 16, 32, 64, 128, 256, 1024]]),
                  ('lr', 0.01, [[0.001, 0.002, 0.004, 0.006, 0.008, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.3, 0.6]]),
                  ('flavor', 'rnn', [['rnn', 'lstm', 'deltarnn', 'fahlmanrnn']]),
                  ('optimizer', 'adagrad', [['sgd', 'adagrad']]),
                  ('embed_size', 512, [[2, 64, 128, 256, 512]]),
                  ('wx_init', 'random', [['random', 'glove300']]),
                  ('num_x_shuffle', 0, [[0, 1, 2, 3, 4, 5, 6, 7]]),
                  ('start_bptt', 7, [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]])]

default_configs_dict = {opt[0]: opt[1] for opt in config_options}

TASK_NAMES = ['sem-cat_task', 'synonym_task', 'match_task']  # TODO remove tasks from rnnlab


def check_configs_dict(configs_dict, new_config_names):
    e = None
    # check if config value in options
    for opt in config_options:
        config_name = opt[0]
        configs_val = configs_dict[opt[0]]
        parts = str(configs_val).split('_')
        allowed_parts_list = [str(p) for p in opt[2]]
        if not len(parts) == len(allowed_parts_list):
            e = 'Missing parts of "{}".'.format(config_name)
        for part_id, (part, allowed_parts) in enumerate(zip(parts, allowed_parts_list)):
            if part not in allowed_parts:
                e = 'Part {} of "{}" must be in {}'.format(part_id + 1, config_name, allowed_parts)
    # syn2sem
    if ('l2m' in configs_dict['syn2sem'] or 'm2l' in configs_dict['syn2sem']) and 'hard' in configs_dict['syn2sem']:
        e = 'Cannot use "hard" in combination with "l2m" or "m2l".'
    if configs_dict['syn2sem'] != 'dist_least_hard' and configs_dict['num_y'] == 1:
        e = 'rnnlab: Did you forget to adjust "num_y"?'
    # do not allow None
    if any([True if new_config is None else False for new_config in new_config_names]):
        e = 'rnnlab: "None" is not allowed in configs file.'
    # task_regime
    for task_name in TASK_NAMES:
        task_lr_config_name = task_name + '_lr'
        if task_name in new_config_names and task_lr_config_name not in new_config_names:
            e = 'rnnlab: Must specify "{}" and "{}" in tandem.'.format(task_name, task_lr_config_name)
    # task_layer_id
    for task_name in TASK_NAMES:
        if task_name in new_config_names and configs_dict['task_layer_id'] + 1 > configs_dict['num_layers']:
            e = 'rnnlab: task_regime is specified, but task_layer_id + 1 > num_layers.'
    # bptt_steps
    if 'bptt_steps' in new_config_names and 'start_bptt' not in new_config_names:
        e = 'rnnlab: Must specify "{}" and "{}" in tandem.'.format('bptt_steps', 'start_bptt')
    # num_layers
    if 'num_layers' in new_config_names and 'task_layer_id' not in new_config_names:
        e = 'rnnlab: Must specify "{}" and "{}" in tandem.'.format('num_layers', 'task_layer_id')
        # error
    if e is not None:
        cprint('{}'.format(e), 'red')
        raise Exception(e)