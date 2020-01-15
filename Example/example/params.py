"""
use only dictionaries to store parameters.
ludwig works on dictionaries and any custom class would force potentially unwanted logic on user.
using non-standard classes here would also make it harder for user to understand.
any custom classes for parameters should be implemented by user in main job function only.
keep interface between user and ludwig as simple as possible
"""

# will submit 3*2=6 jobs, each using a different learning rate and "configuration"
param2requests = {
    'learning_rate': [0.1, 0.2, 0.3],
    'configuration': [(1, 0), (0, 1)],  # inner collections must be of type tuple, not list
}


param2default = {
    'learning_rate': 0.1,
    'configuration': (1, 0),
}