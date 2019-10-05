import unittest
import os

from ludwig import config
from ludwig.__main__ import submit


class MyTest(unittest.TestCase):

    example_root_path_name = str(config.Dirs.root / 'Example')

    def test_submit(self):
        """
        submit job from  Example project.
        if this function fails, something is wrong with job submission logic.
        """

        os.chdir(self.example_root_path_name)
        submit(src='example', worker='hawkins')

        return True


if __name__ == '__main__':
    unittest.main()