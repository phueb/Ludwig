import unittest
import os
from pathlib import Path

from ludwig import configs
from ludwig.uploader import Uploader
from ludwig.job import Job
from Example.example import params


class MyTest(unittest.TestCase):

    @staticmethod
    def test_submit():
        """
        submit job from  Example project.
        if this function fails, something is wrong with job submission logic.
        """
        project_name = 'Example'
        src_name = 'example'
        # project path is always on shared drive when not running locally
        project_path = Path('/') / 'media' / 'ludwig_data' / project_name
        if not project_path.exists():
            project_path.mkdir()
        worker = configs.Remote.online_worker_names[0]
        runs_path = project_path / configs.Constants.runs

        os.chdir(str(project_path))
        uploader = Uploader(project_path, src_name)
        
        job = Job(params.param2default)
        job.update_param_name(runs_path, num_new=0)
        job.update_job_name_and_save_path(0, src_name)
        job.param2val['project_path'] = configs.WorkerDirs.ludwig_data / project_name
        
        uploader.to_disk(job, worker)

        return job.is_ready()


if __name__ == '__main__':
    unittest.main()