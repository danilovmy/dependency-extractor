from pathlib import Path
from base import init

if __name__ == '__main__':
    for project in ('python', ):
        folder = Path(__file__).parent / f'legacy_{project}'
        LOC = 0
        SLOC = 0
        LLOC = 0
        idx = 0
        for idx, filename in enumerate(folder.glob('**/*.py'), start=1):
            root = init(filename)
            LOC += root.LOC
            SLOC += root.SLOC
            LLOC += root.LLOC

        print('project', project, 'total files', idx, 'LOC', LOC, 'SLOC', SLOC, 'LLOC', LLOC)
