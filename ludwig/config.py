from pathlib import Path
import socket
import sys

from ludwig import try_mounting

if 'win' in sys.platform:
    raise SystemExit('Ludwig does not support Windows')
elif 'linux' == sys.platform:
    mnt_point = '/media'
else:
    # assume MacOS
    mnt_point = '/Volumes'


class Dirs:
    root = Path(__file__).parent.parent
    if try_mounting:
        research_data = Path(mnt_point) / 'research_data'
        stdout = research_data / 'stdout'
        watched = Path('/var/sftp/ludwig_jobs')
    else:
        print("Ludwig: Not trying to mount {}/research_data".format(mnt_point))


class SFTP:
    watched_pattern = 'run*.py'  # this is required for watcher to know which file to run
    private_key_pass_path = Path.home() / '.rsapub_passwd'

    # TODO yash is using lecun
    worker_names = ['hoff', 'norman', 'hebb', 'hinton', 'pitts', 'hawkins', 'bengio']


class Time:
    delete_delta = 24  # hours
    format = '%Y-%m-%d-%H-%M-%S'


class CLI:
    num_top_processes = 5
    num_stdout_lines = 10


hostname = socket.gethostname()