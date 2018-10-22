from pathlib import Path
import socket


class Dirs:
    lab = Path('/') / 'media' / 'lab'
    stdout = lab / 'stdout'
    watched = '/var/sftp/ludwig'


class SFTP:
    worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'lecun', 'bengio']
    watched_fname = 'run.py'  # this is required for watcher to know which file to run
    private_key_pass_path = Path.home() / '.rsapub_passwd'


hostname = socket.gethostname()