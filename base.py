from dataclasses import dataclass, field
from pathlib import Path
import ast

import argparse
import sys

@dataclass
class ASTObject:
    """ Base wrapper for AST Node for complexity measurements"""
    name: str
    reflection: ast.AST = None  # AST object, prototyped this instance
    parent: 'ASTObject' = None
    path: Path = None  # where placed
    source_lines: list[str] = None # source file line per line content
    children: list = field(default_factory=list)

    @property
    def docstring(self):
        return (ast.get_docstring(self.reflection) or  '').strip()

    def setup(self):
        self.path = self.path or self.parent.path
        for node in ast.iter_child_nodes(self.reflection):
            self.collect(node)
        return self

    def collect(self, node):
        self.children.append(type(self)(f'Child Node {node.__class__.__name__} of {self.name}', node, self).setup())
        return self.children[-1]

    @property
    def source(self):
        return self.source_lines or (self.parent and self.parent.source) or []

    @property
    def raw_lines(self):
        return self.source[max(0, self._start - 1): self._end]

    @property
    def raw_weight(self):
        return self._end - max(0, self._start - 1)  # csl
    LOC = raw_weight  # The number of source lines

    @property
    def source_code_weight(self):
        return self.LOC - self.comments -self.spaces # csl
    SLOC = source_code_weight  # The number of source lines of code

    @property
    def code(self):
        """
        Trying to unparse a highly complex expression would result with RecursionError.
        more details: https://docs.python.org/3/library/ast.html#ast.unparse
        """
        raw = ast.unparse(self.reflection).splitlines()
        return [line for line in raw if line.strip()]

    @property
    def code_weight(self):
        return len(self.code)
    LLOC = code_weight # The number of logical lines of code

    def get_path(self):
        """ Path to source file containing this object """
        return self.path or self.parent.get_path()

    @property
    def _end(self):
        if hasattr(self.reflection, 'end_lineno') and self.reflection.end_lineno:
            return self.reflection.end_lineno
        if hasattr(self.reflection, 'body') and self.reflection.body:
            return type(self)('test', self.reflection.body[-1], self)._end
        return self._start

    @property
    def decorators(self):
        return type(self)('decorators', ast.stmt(body=self.reflection.decorator_list if self.is_decorated else []))

    @property
    def is_decorated(self):
        return hasattr(self.reflection, 'decorator_list') and len(self.reflection.decorator_list)

    @property
    def _start(self):
        if hasattr(self.reflection, 'lineno'):
            return self.reflection.lineno - (self.decorators.LOC if self.is_decorated else 0)
        if hasattr(self.reflection, 'body') and self.reflection.body:
            return type(self)('test', self.reflection.body[0], self)._start
        return 0

    @property
    def spaces(self, response = 0):
        if self.source:
            for line in self.raw_lines:
                response += not len(line.strip())
        return response

    @property
    def comments(self, response = 0):
        if self.source:
            for line in self.raw_lines:
                response += line.strip().startswith('#')
        return response

    def _start_module(self, node):
        if self.collect_modules(node):
            start_node = ast.increment_lineno(ast.fix_missing_locations(ast.Expr('')), -1)
            self.children.insert(0, ASTObject(f'Start Node for {self.name}', start_node, self).setup())
        return self

    @classmethod
    def init(cls, path):
        path = Path(path)
        try:
            source = path.read_text(encoding='utf-8')
            node = ast.parse(source, filename=str(path.absolute()))
        except Exception as error:
            print(f"Could not read or parse {path}: {error}", file=sys.stderr)
            source, node = '', ast.parse('"""Error"""', filename=str(path.absolute()))
        return cls('root', node, path=path, source_lines=source.splitlines()).setup()

    def render(self, ready=False):
        try:
            render = '\n'.join([child.render() for child in self.children])
            response = f'<details style="padding-left:3em;"><summary>{getattr(self.reflection, "name", getattr(self.reflection,"id", self.reflection.__class__.__name__))}</summary>{self.name}<br>{render}</details>'
            return f'<html><body>{response}</body></html>' if ready else response
        except:
            ...

def main(cls=ASTObject, args=None):
    args = args or sys.argv
    if len(args) < 2:
        print(f"Usage: {sys.argv[0]} <python_file.py>")
        try:
            args = [sys.modules[cls.__module__].__file__]
        except:
            args = [__file__]
    else:
        args = args[1:]


    parser = argparse.ArgumentParser(prog='cognitive_complexity.py', description='Compute Cognitive Complexity (Sonar-like) for Python files.')
    parser.add_argument('paths', nargs='+', help='Python file(s) or directories to analyze.')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recurse into directories.')
    args = parser.parse_args(args)

    objects = []
    for path in args.paths:
        path = Path(path)
        if path.is_file():
            if path.suffix == '.py':
                objects.append(cls.init(path))
            else:
                print(f"Skipping non-Python file: {path}")  # other files like stubs not implemented yet
        elif path.is_dir():
            template = '**/*.py' if args.recursive else '*.py'
            for path in path.glob(template):
                objects.append(cls.init(path))

    return objects

if __name__ == '__main__':
    root, *__ = main()
    print('LOC', root.LOC)
    print('blank lines', root.spaces)
    print('comments', root.comments)
    print('SLOC', root.SLOC)
    print('LLOC', root.LLOC)
    print(root.docstring)
