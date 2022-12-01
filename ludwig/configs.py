from pathlib import Path
import socket


class WorkerDirs:
    root = Path(__file__).parent.parent
    ludwig_data = Path('/') / 'media' / 'ludwig_data'  # relative to worker
    stdout = ludwig_data / 'stdout'
    watched = Path('/') / 'var' / 'sftp' / 'ludwig_jobs'


class Remote:
    watched_pattern = 'run*.py'  # this is required for watcher to know which file to run
    path_to_ssh_config = Path.home() / '.ssh' / 'ludwig_config'
    online_worker_names = ['norman', 'hinton', 'pitts', 'hawkins', 'hoff', 'bengio', 'hebb',]  # TODO lecun does not have access to internet
    all_worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio', 'lecun']
    group2workers = {'half1': ['hoff', 'norman', 'hebb', 'hinton'],
                     'half2': ['pitts', 'hawkins', 'bengio', 'lecun']}
    disk_max_percent = 90


class Time:
    delete_delta = 24  # hours
    format = '%Y-%m-%d-%H:%M:%S'


class Constants:
    param2val = 'param2val'
    saves = 'saves'
    runs = 'runs'
    added_param_names = ['job_name', 'param_name', 'project_path', 'save_path']

    worker2ip = {
        'bengio': '130.126.181.116',
        'hinton': '130.126.181.117',
        'hoff': '130.126.181.118',
        'norman': '130.126.181.119',
        'hawkins': '130.126.181.120',
        'hebb': '130.126.181.121',
        'pitts': '130.126.181.122',
        'lecun': '130.126.181.123',
    }


hostname = socket.gethostname()