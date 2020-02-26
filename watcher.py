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
import psutil
import socket

from ludwig import config

hostname = socket.gethostname()


def custom_print(string):
    sys.stdout.flush()
    print('{:<20} Ludwig ({:<8}): {}'.format(datetime.datetime.now().strftime(config.Time.format),
                                             hostname,
                                             string))
    sys.stdout.flush()


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.thread = None
        self.q = Queue()
        self.run_pattern = re.compile('(run)')
        self.time_stamps = [datetime.datetime.now()]

    def start(self):
        self.thread = threading.Thread(target=self._process_q)
        self.thread.daemon = True
        self.thread.start()

    def on_any_event(self, event):
        if self.run_pattern.match(Path(event.src_path).name):  # True if detected event concerns run_*.py
            # sftp produces 2 events within 1 sec - ignore 2nd event
            ts = datetime.datetime.now()
            time_delta = ts - self.time_stamps.pop()
            if time_delta.total_seconds() < 1:
                # Ignoring trigger event because it happened less than 1 sec after previous
                pass
            else:
                custom_print('Killing "{}"'.format(event.src_path))  # TODO test
                self.stop_active_jobs(event.src_path)
                custom_print('Adding to queue: {}'.format(event.src_path))
                self.q.put(event)
            self.time_stamps.append(ts)

    @staticmethod
    def housekeeping():
        delta = datetime.timedelta(hours=config.Time.delete_delta)
        time_of_init_cutoff = datetime.datetime.now() - delta

        # TODO what exactly needs to be deleted?

    @staticmethod
    def stats():
        ps = []
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name', 'username'])
                pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
                ps.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by 'vms' (virtual memory usage)
        ps = sorted(ps, key=lambda p: p['vms'], reverse=True)  # a list of processes, including their 'vms'

        # TODO use this function to calculate overall memory usage,
        #  to determine if jobs should be allowed to run simultaneously

    @staticmethod
    def stop_active_jobs(event_src_path):
        command = 'pkill -f -c {}'.format(event_src_path)
        num_killed = subprocess.getoutput(command)
        custom_print('Killed {} process(es)'.format(num_killed))

    @staticmethod
    def start_jobs(event_src_path):
        custom_print('Executing "{}"'.format(event_src_path))

        command = 'python3.7 {}'.format(event_src_path)

        try:
            subprocess.check_call([command], shell=True)  # stdout is already redirected, cannot do it here
        except CalledProcessError as e:  # this is required to continue to the next item in queue if current item fails
            custom_print(str(e))
            custom_print('Failed to execute: {}'.format(command))
            print()
        else:
            custom_print('Successfully executed: {}'.format(command))
            print()

    def _process_q(self):

        while True:
            event = self.q.get()
            self.housekeeping()
            self.start_jobs(event.src_path)


def main():
    custom_print('Started Ludwig/watcher.py')
    sys.stdout.flush()
    observer = Observer()
    handler = Handler()
    handler.start()

    observer.schedule(handler, str(config.WorkerDirs.watched), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == '__main__':
    p = Path(config.WorkerDirs.stdout)
    if not p.exists():
        p.mkdir(parents=True)
    main()
