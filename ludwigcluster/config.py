from pathlib import Path
import socket


class Dirs:
    research_data = Path('/') / 'media' / 'research_data'
    stdout = research_data / 'stdout'
    watched = Path('/var/sftp/ludwig')


class SFTP:
    # TODO yash is using lecun
    worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio']
    watched_pattern = 'run*.py'  # this is required for watcher to know which file to run
    private_key_pass_path = Path.home() / '.rsapub_passwd'


class Time:
    delete_delta = 24  # hours
    format = '%Y-%m-%d-%H-%M-%S'


hostname = socket.gethostname()