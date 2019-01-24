from pathlib import Path


class Dirs:
    root = Path(__file__).parent.parent
    src = root / 'src'
    tasks = root / 'tasks'
    corpora = root / 'corpora'
    #
    remote_root = Path('/') / 'media' / 'lab' / 'your_project_name'
    runs = remote_root / 'runs'
    backup = remote_root / 'backup'