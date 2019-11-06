from pathlib import Path
import socket

from ludwig import try_mounting


class WorkerDirs:
    root = Path(__file__).parent.parent
    if try_mounting:
        research_data = Path('/media') / 'research_data'
        stdout = research_data / 'stdout'
        watched = Path('/var/sftp/ludwig_jobs')
    else:
        print("Ludwig: Not trying to mount media/research_data")


class SFTP:
    watched_pattern = 'run*.py'  # this is required for watcher to know which file to run
    path_to_ssh_config = Path.home() / '.ssh' / 'ludwig_config'
    online_worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'hawkins', 'bengio']
    all_worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio', 'lecun']

    # note: Yash is using pitts, and lecun


class Time:
    delete_delta = 24  # hours
    format = '%Y-%m-%d-%H-%M-%S'


class CLI:
    num_top_processes = 5
    num_stdout_lines = 10


hostname = socket.gethostname()