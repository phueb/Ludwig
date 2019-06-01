from pathlib import Path


class RemoteDirs:
    root = Path('/media/lab') / 'your_module_folder_name'
    runs = root / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'your_module_name'
    runs = root / '{}_runs'.format(src.name)