"""
The Uploader is used to submit jobs to one or more workers at the UIUC Learning & Language Lab
An sftp-client library is used to upload code files to each machine.
"""
from pathlib import Path
import pysftp
import platform
import psutil
import pickle
from typing import List, Dict, Optional, Any, Tuple

from ludwig import config
from ludwig import print_ludwig
from ludwig import run
from ludwig.job import Job


class Uploader:
    def __init__(self,
                 project_path: Path,
                 src_name: str,
                 ):
        self.project_path = project_path
        self.project_name = project_path.name
        self.src_name = src_name
        self.runs_path = self.project_path / 'runs'
        self.worker2ip = self.make_worker2ip()

    def remove_existing_jobs(self):
        """
        remove existing parameter configurations saved to disk.
        WARNING: Do not call this when running locally,
        as this will remove jobs to be run on Ludwig workers

        """
        for pkl_path in self.project_path.glob('*.pkl'):
            pkl_path.unlink()

    @staticmethod
    def make_worker2ip():
        """load hostname aliases from .ssh/ludwig_config"""
        res = {}
        h = None
        p = config.Remote.path_to_ssh_config
        if not p.exists():
            raise FileNotFoundError('Please specify hostname-to-IP mappings in {}'.format(p))
        with p.open('r') as f:
            for line in f.readlines():
                words = line.split()
                if 'Host' in words:
                    h = line.split()[1]
                    res[h] = None
                elif 'HostName' in words:
                    ip = line.split()[1]
                    res[h] = ip
        return res

    def check_disk_space(self, verbose=False):
        if platform.system() in {'Linux'}:
            p = self.project_path.parent
            usage_stats = psutil.disk_usage(str(p))
            percent_used = usage_stats[3]
            if verbose:
                print_ludwig('Percent Disk Space used at {}: {}'.format(p, percent_used))
            if percent_used > config.Remote.disk_max_percent:
                raise RuntimeError('Disk space usage > {}.'.format(config.Remote.disk_max_percent))
        else:
            print_ludwig('WARNING: Cannot determine disk space on non-Linux platform.')

    def to_disk(self,
                job: Job,
                worker: Optional[str] = None,
                ) -> None:
        """
        saves parameter configuration for a single job to project_path.
        This allows Ludwig workers to find jobs
        """
        if not job.is_ready():
            raise SystemExit('Cannot save job. Job is not ready. Update job.param2val')

        # save parameter configuration to shared drive
        unique_id = f'{job.param2val["param_name"]}_{job.param2val["job_name"]}'
        p = self.project_path / f'{worker}_{unique_id}.pkl'
        with p.open('wb') as f:
            pickle.dump(job.param2val, f)

        # console
        print_ludwig(f'Parameter configuration for {worker} saved to disk')
        print(job)
        print()

    def upload(self, worker):
        """
        source code is uploaded.
        run.py is uploaded.
        modification of run.py on worker triggers watcher.py, adding run.py to queue
        """

        # -------------------------------------- checks

        assert self.project_name.lower() == self.src_name  # TODO what about when src name must be different?
        # this must be true because in run.py project_name is converted to src_name

        self.check_disk_space()

        # -------------------------------------- prepare paths

        if not self.project_path.exists():
            self.project_path.mkdir()
        if not self.runs_path.exists():
            self.runs_path.mkdir(parents=True)

        remote_path = f'{config.WorkerDirs.watched.name}/{self.src_name}'
        print_ludwig(f'Will upload {self.src_name} to {remote_path}')

        # ------------------------------------- sftp

        # connect via sftp
        research_data_path = self.project_path.parent
        private_key_path = research_data_path / '.ludwig' / 'id_rsa'
        sftp = pysftp.Connection(username='ludwig',
                                 host=self.worker2ip[worker],
                                 private_key=str(private_key_path))

        sftp.makedirs(remote_path)
        sftp.put_r(localpath=self.src_name, remotepath=remote_path)

        # upload run.py
        run_file_name = f'run_{self.project_name}.py'
        sftp.put(localpath=run.__file__,
                 remotepath=f'{config.WorkerDirs.watched.name}/{run_file_name}')
        print_ludwig(f'Upload to {worker} complete')
        print()