from stats import ASTObject as baseASTObject
from pathlib import Path
from collections import Counter

copy_pasta = Counter()

class ASTObject(baseASTObject):

    @property
    def copy_paste(self):
        for line in self.source_lines:
            line = line.strip()[:245]
            if line:
                copy_pasta.update([line])
        return copy_pasta.most_common()


def main(path):
    root = Path(path).parent
    for source in root.glob('**/*.py'):
        ASTObject.init(source).copy_paste

if __name__ == '__main__':
    path = Path('core1.py')
    main(path)
    print(copy_pasta.most_common()[:10])