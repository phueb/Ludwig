from pathlib import Path
import socket


class WorkerDirs:
    root = Path(__file__).parent.parent
    research_data = Path('/') / 'media' / 'research_data'
    stdout = research_data / 'stdout'
    watched = Path('/') / 'var' / 'sftp' / 'ludwig_jobs'


class Remote:
    watched_pattern = 'run*.py'  # this is required for watcher to know which file to run
    path_to_ssh_config = Path.home() / '.ssh' / 'ludwig_config'
    online_worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio', 'lecun']
    all_worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio', 'lecun']
    disk_max_percent = 90


class Time:
    delete_delta = 24  # hours
    format = '%Y-%m-%d-%H:%M:%S'


class Constants:
    param2val = 'param2val'
    not_ludwig = '_not-ludwig'
    saves = 'saves'
    runs = 'runs'
    added_param_names = ['job_name', 'param_name', 'project_path', 'save_path']


hostname = socket.gethostname()