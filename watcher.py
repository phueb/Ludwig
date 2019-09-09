from datetime import datetime
import threading
import time
from subprocess import CalledProcessError
import subprocess
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from queue import Queue
import sys
import re
import datetime
import shutil

from ludwigcluster import config


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.thread = None
        self.q = Queue()
        self.watched_pattern = re.compile('(run)')

    def start(self):
        self.thread = threading.Thread(target=self._process_q)
        self.thread.daemon = True
        self.thread.start()

    def on_any_event(self, event):
        is_trigger_event = self.watched_pattern.match(Path(event.src_path).name)
        if is_trigger_event:
            ts = datetime.datetime.now()
            self.q.put((event, ts))

    @staticmethod
    def delete_params_dirs():
        print('LudwigCluster: Deleting job_dirs more than {} hours old...'.format(config.Time.delete_delta))
        delta = datetime.timedelta(hours=config.Time.delete_delta)
        time_of_init_cutoff = datetime.datetime.now() - delta
        for job_p in config.Dirs.watched.rglob('*num*'):
            result = re.search('_(.*)_', job_p.name)
            time_of_init = result.group(1)
            dt = datetime.datetime.strptime(time_of_init, config.Time.format)
            if dt < time_of_init_cutoff:
                print('LudwigCluster: {} is more than {} hours old. Removing'.format(job_p.name, config.Time.delete_delta))
                shutil.rmtree(str(job_p))

    def start_run(self, event_src_path):
        self.delete_params_dirs()
        sys.stdout.flush()

        command = 'python3 {}'.format(event_src_path)

        try:
            subprocess.check_call([command], shell=True)  # stdout is already redirected, cannot do it here
        except CalledProcessError as e:  # this is required to continue to the next item in queue if current item fails
            print(e)
        else:
            print('LudwigCluster: Successfully executed: {}'.format(command))
            print()
            sys.stdout.flush()

    def _process_q(self):
        last_ts = datetime.datetime.now()

        while True:
            print('LudwigCluster: Checking queue')
            event, time_stamp = self.q.get()
            time_delta = time_stamp - last_ts
            if time_delta.total_seconds() < 1:  # sftp produces 2 events within 1 sec - ignore 2nd event
                print('LudwigCluster: Ignoring 2nd event.')
                continue
            else:
                sys.stdout.flush()
                print('LudwigCluster: Detected event {} at {}'.format(event.src_path, datetime.datetime.now()))
                print('LudwigCluster: Executing "{}"'.format(event.src_path))
                sys.stdout.flush()

            self.start_run(event.src_path)
            last_ts = time_stamp


def watcher():
    print('LudwigCluster: Started LudwigCluster/watcher.py')
    sys.stdout.flush()
    observer = Observer()
    handler = Handler()
    handler.start()

    observer.schedule(handler, str(config.Dirs.watched), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == '__main__':
    p = Path(config.Dirs.stdout)
    if not p.exists():
        p.mkdir(parents=True)
    watcher()
