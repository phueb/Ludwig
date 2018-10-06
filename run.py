from pathlib import Path

from src.task import countup
from src.task import save_file

countup(5)

p = Path('/') / 'media' / 'lab' / 'hello.txt'
save_file(p)
