from pathlib import Path


class Dirs:
    lab = Path('/') / 'media' / 'lab'


class SFTP:
    watched_fname = 'run.py'
    private_key_pass_path = Path.home() / '.rsapub_passwd'