import unittest
import os

from ludwig import config
from ludwig.__main__ import submit


class MyTest(unittest.TestCase):

    def test_submit(self):

        example_root_path_name = str(config.Dirs.root / 'Example')
        os.chdir(example_root_path_name)

        print(os.getcwd())

        submit(src='example', worker='hawkins')


if __name__ == '__main__':
    unittest.main()