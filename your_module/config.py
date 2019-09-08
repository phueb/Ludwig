from pathlib import Path


class RemoteDirs:
    root = Path('/media/research_data') / 'Your_Module'
    runs = root / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'your_module'
    runs = root / '{}_runs'.format(src.name)