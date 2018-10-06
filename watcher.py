from datetime import datetime
import threading
import time
import subprocess
from pathlib import Path

from os.path import expanduser, normpath

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from queue import Queue

import socket
hostname = socket.gethostname()

PROJECT_NAME = 'LudwigCluster'
LOGGING_DIR = '/media/lab/{}'.format(PROJECT_NAME)
LOGGING_FNAME = '{}_stdout.txt'.format(hostname)
CMD = 'python3 /var/sftp/{}/run.py > {}/{}'.format(PROJECT_NAME, LOGGING_DIR, LOGGING_FNAME)
WATCH_FILE_NAME = 'run.py'


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.thread = None
        self.q = Queue()

    def start(self):
        self.thread = threading.Thread(target=self._process_q)
        self.thread.daemon = True
        self.thread.start()

    def on_any_event(self, event):
        global stopped

        norm = normpath(expanduser(event.src_path))
        if not event.is_directory and norm == WATCH_FILE_NAME:
            ts = datetime.now()
            self.q.put((event, ts))

    def trigger(self):
        try:
            subprocess.check_call([CMD], shell=True)
        except OSError as exc:
            print(exc)

    def _process_q(self):
        last_ts = datetime.now()

        while True:
            event, time_stamp = self.q.get()
            time_delta = time_stamp - last_ts
            if time_delta.total_seconds() < 1:  # sftp prdocues 2 events within 1 sec - ignore 2nd event
                continue

            print('Executing "{}"'.format(CMD))
            self.trigger()
            last_ts = time_stamp
            print('Done\n')


def watcher():
    print('Started file-watcher. Upon change, run.py will be executed.')
    observer = Observer()
    handler = Handler()
    handler.start()

    observer.schedule(handler, '.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == '__main__':
    p = Path(LOGGING_DIR)
    if not p.exists():
        p.mkdir(parents=True)
    watcher()


# TODO it's probably best not to execute neural network task until completion
# TODO it might be more flexible to allow restarting of task upon file change
