from pathlib import Path

from ludwigcluster import PROJECT_NAME


class Dirs:
    lab = Path('/') / 'media' / 'lab' / PROJECT_NAME
    src = Path().cwd() / PROJECT_NAME


class Interface:
    common_timepoint = 1