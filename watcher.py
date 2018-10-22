from datetime import datetime
import threading
import time
import subprocess
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from queue import Queue

from ludwigcluster import config


CMD = 'python3 {}/{}'.format(config.Dirs.watched, config.SFTP.watched_fname)

# TODO it might be better to allow restarting of task upon file change (if a long running task is no longer wanted)


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.thread = None
        self.q = Queue()

    def start(self):
        self.thread = threading.Thread(target=self._process_q)
        self.thread.daemon = True
        self.thread.start()

    def on_any_event(self, event):
        is_trigger_event = Path(config.Dirs.watched) / config.SFTP.watched_fname == Path(event.src_path)
        print('Detected event {}'.format(event.src_path))
        print('is trigger event: {}'.format(is_trigger_event))
        if is_trigger_event:
            ts = datetime.now()
            self.q.put((event, ts))

    def trigger(self):
        fname = '{}_stdout_{}.txt'.format(config.hostname, datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))
        cmd = CMD + ' > {}/{}'.format(config.Dirs.stdout, fname)
        try:
            subprocess.check_call([cmd], shell=True)
        except OSError as exc:
            print(exc)

    def _process_q(self):
        last_ts = datetime.now()

        while True:
            event, time_stamp = self.q.get()
            time_delta = time_stamp - last_ts
            if time_delta.total_seconds() < 1:  # sftp produces 2 events within 1 sec - ignore 2nd event
                continue

            print('Executing "{}"'.format(CMD))
            self.trigger()
            last_ts = time_stamp
            print('Done\n')


def watcher():
    print('Started file-watcher. Upon change, {} will be executed.'.format(config.SFTP.watched_fname))
    observer = Observer()
    handler = Handler()
    handler.start()

    observer.schedule(handler, config.Dirs.watched, recursive=False)
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