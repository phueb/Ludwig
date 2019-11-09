import unittest
import os
from pathlib import Path

from ludwig import config
from ludwig.uploader import Uploader  # import client after modifying config.is_unit_test
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
        example_project_path = Path(__file__).parent.parent / project_name
        worker = config.Remote.online_worker_names[0]
        runs_path = example_project_path / config.Constants.runs

        os.chdir(str(example_project_path))
        uploader = Uploader(example_project_path, src_name)
        
        job = Job(params.param2default)
        job.update_param_name(runs_path, num_new=0)
        job.update_job_name(0)
        job.param2val['project_path'] = config.WorkerDirs.research_data / project_name
        
        uploader.to_disk(job, worker)

        return job.is_ready()


if __name__ == '__main__':
    unittest.main()