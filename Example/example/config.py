from pathlib import Path
import sys

if 'win' in sys.platform:
    raise SystemExit('Not supported on Windows')
elif 'linux' == sys.platform:
    mnt_point = '/media'
else:
    # assume MacOS
    mnt_point = '/Volumes'


class RemoteDirs:
    research_data = Path(mnt_point) / 'research_data'
    root = research_data / 'Example'
    runs = root / 'runs'


class LocalDirs:
    root = Path(__file__).parent.parent
    src = root / 'example'
    runs = root / '{}_runs'.format(src.name)


class Global:
    debug = False
    local = False