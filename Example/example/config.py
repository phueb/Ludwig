from pathlib import Path
import sys
import os

if sys.platform == 'darwin':
    default_mnt_point = '/Volumes'
elif sys.platform == 'linux':
    default_mnt_point = '/media'
else:
    if not os.getenv('LUDWIG_MNT'):
        raise EnvironmentError('Missing LUDWIG_MNT environment variable')


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'example'


class Global:
    debug = False