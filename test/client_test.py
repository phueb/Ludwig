import unittest
import os
from pathlib import Path

from ludwig import config
from ludwig.uploader import Uploader  # import client after modifying config.is_unit_test
from ludwig.job import Job

from Example.example import params


class MyTest(unittest.TestCase):

    project_name = 'Example'
    src_name = 'example'
    example_project_path = Path(__file__).parent.parent / project_name
    worker = config.Submit.online_worker_names[0]

    def test_submit(self):
        """
        submit job from  Example project.
        if this function fails, something is wrong with job submission logic.
        """

        os.chdir(str(self.example_project_path))
        uploader = Uploader(self.example_project_path, self.src_name)
        job = Job(params.param2default, self.example_project_path, n=0)
        job.param2val['project_path'] = config.WorkerDirs.research_data / self.project_name
        uploader.upload(job, self.worker, no_upload=True)

        return True


if __name__ == '__main__':
    unittest.main()