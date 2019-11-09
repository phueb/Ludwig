from pathlib import Path
import os
import sys

# mount point
if sys.platform == 'darwin':
    default_mnt_point = '/Volumes'
elif sys.platform == 'linux':
    default_mnt_point = '/media'
else:
    # unknown default - user must specify mount point via environment variable
    default_mnt_point = os.environ['LUDWIG_MNT']