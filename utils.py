from pathlib import Path
from argparse import ArgumentParser

SOURCES = Path('legacy/')
RESULTS = Path('logs/')

def validate_filename(filename):
    """Validate filenames to obtain type-hints in files."""
    path = Path(filename)
    if not path.exists():
        raise ValueError("Path to observe files for type hints should exist, use --help to see more.")
    if path.is_file() and not path.suffix == '.py':
        raise ValueError("File to observe for type hints should be a .py file, use --help to see more.")
    return path


parser = ArgumentParser(prog='Entry point for hints collector', description='This ist script to check type hints in any python file or folder', epilog='Type hints collected')
parser.add_argument('filenames', type=validate_filename, nargs='*', help='Path to the folder or file to collect type-hints. By default hints are collected in : `%(default)s` in current directory.', default=[SOURCES])
parser.add_argument("-o", "--output", type=str, help='Path to the folder where you can store RESULTS. By default RESULTS are collected in : `%(default)s` in current directory .', default=RESULTS, required=False)

def parents(path):
    root = Path()
    for directory in path.parts:
        root = root / directory
        if not root.exists():
            root.mkdir()
        if root.is_dir():
            yield root

def initiate(module):
    if module.is_file():
        module = module.parent
    init = module / '__init__.py'
    if not init.exists():
        init.touch()


def base_init(*routes):
    for path in routes:
        if path.suffix:
            path = path.parent
        for parent in parents(path):
            initiate(parent)
        for module in path.rglob('*.py'):
            for parent in parents(module):
                initiate(parent)
