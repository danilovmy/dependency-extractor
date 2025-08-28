from base import ASTObject, init
from pathlib import Path
import ast
from readability import Readability

class ReadableAST(ASTObject):

    def readability(self, method='flesch_kincaid', *args, **kwargs):
        if self.source:
            pipe = (line.strip() for line in self.source)
            not_empty = (line for line in pipe if line)
            text = '. '.join(not_empty).strip()
            if text:
                lexer = Readability(text)
                try:
                    return getattr(lexer, method)(*args, **kwargs).score
                except Exception as _error:
                    pass
        return 0


if __name__ == '__main__':
    path = Path(__file__)
    root = init(path, cls=ReadableAST)
    print('LOC', root.LOC)
    print('blank lines', root.spaces)
    print('comments', root.comments)
    print('SLOC', root.SLOC)
    print('LLOC', root.LLOC)

    if root.classes:
        cls =root.classes[0]
        if cls.children:
            child = cls.children[0]
            print(child.is_docstring)


