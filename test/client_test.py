import unittest
import os
from pathlib import Path

from ludwig import config
from ludwig.client import Client  # import client after modifying config.is_unit_test

from Example.example import params


class MyTest(unittest.TestCase):

    project_name = 'Example'
    example_root_path_name = str(config.RemoteDirs.root / project_name)

    def test_submit(self):
        """
        submit job from  Example project.
        if this function fails, something is wrong with job submission logic.
        """

        os.chdir(self.example_root_path_name)

        client = Client(self.project_name, params.param2default, unittest=True)
        client.submit(src_name='example',  # uploaded to workers
                      extra_folder_names=['third_party_code'],  # uploaded to shared drive not workers
                      param2requests=params.param2requests,
                      reps=1,
                      worker='bengio',
                      no_upload=True)

        return True


if __name__ == '__main__':
    unittest.main()