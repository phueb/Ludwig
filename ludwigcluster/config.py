from pathlib import Path

class Dirs:
    lab = Path('/') / 'media' / 'lab'


class SFTP:
    worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'lecun', 'bengio']
    watched_fname = 'run.py'  # this is required for watcher to know which file to run
    private_key_pass_path = Path.home() / '.rsapub_passwd'