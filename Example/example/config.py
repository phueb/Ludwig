from pathlib import Path


class RemoteDirs:
    root = Path('/media/research_data') / 'Example'
    runs = root / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'example'
    runs = root / '{}_runs'.format(src.name)


class Global:
    debug = False