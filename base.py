from dataclasses import dataclass, field
from pathlib import Path
import ast

from halsted import HalsteadVisitor


@dataclass
class ASTObject:
    """ Base wrapper for AST Node for complexity measurements"""
    PIPELINE = 'collect_modules', 'collect_imports', 'collect_classes', 'collect_functions', 'collect_constants', 'collect_values'

    name: str
    reflection: ast.AST = None  # AST object, prototyped this instance
    parent: 'ASTObject' = None
    mentioned: dict = field(default_factory=dict)  # used in type hints
    dependencies: dict = field(default_factory=dict)  # used dependencies
    path: Path = None  # where placed

    importlib: bool = False  # if importlib used in this reflection
    shortcut: str = ''
    _attributes: dict = None  # declared attributes
    _constants: dict = None  # declared constants
    _properties: dict = None # declared properties
    _imports: dict = field(default_factory=list)  # imported
    _classes: list = field(default_factory=list)
    children: list = field(default_factory=list)
    _functions: list = field(default_factory=list)
    source_lines: list[str] = field(default_factory=list) # source file line per line content

    @property
    def have_internals(self):
        """ if declared functions or classes internal """
        if self.is_function and bool(len(self.classes) + len(self.functions)):
            return True
        return any(child.have_internals for child in self.children)

    @property
    def docstring(self):
        return (ast.get_docstring(self.reflection) or  '').strip()

    @property
    def is_docstring(self):
        if isinstance(self.reflection, ast.Expr):
            return hasattr(self.reflection, 'value') and isinstance(self.reflection.value, ast.Constant)

    @property
    def have_imports(self):
        """ if declared functions or classes internal """
        return len(self._imports) or any(child.have_imports for child in self.children)

    def setup(self):
        self.path = self.path or self.parent.path
        for node in ast.iter_child_nodes(self.reflection):
            self.collect(node)
            __processing = any(getattr(self, pipe)(node) for pipe in self.PIPELINE)  # we dont need a result
        return self

    def collect_modules(self, node):
        if isinstance(node, (ast.Module)):
            return node

    def collect(self, node):
        self.children.append(ASTObject(f'Child Node {node.__class__.__name__} of {self.name}', node, self).setup())
        return self.children[-1]

    def collect_imports(self, node):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            self._imports.append(ASTObject(f'ImportLine {node.__class__.__name__}', node, self).setup())
            if isinstance(node, ast.ImportFrom):
                if 'importlib' in (node.module or '.'):
                    self.importlib = True
                    print('importlib detected on line No: ', node.lineno, '. File name: ', self.path, )
            elif isinstance(node, ast.Import):
                if any('importlib' in alias.name for alias in node.names):
                    self.importlib = True
                    print('importlib detected on line No: ', node.lineno, '. File name: ', self.path, )
            else:
                raise NotImplementedError( f'Import type {type(node).__name__} not implemented yet')
            return node

    def importlib_detected(self, node):
        return self.importlib or any(child.importlib for child in self.children)

    def collect_classes(self, node):
        if isinstance(node, (ast.ClassDef)):
            self._classes.append(ASTObject(node.name, node, self).setup())
            return node

    @property
    def is_class(self):
        return isinstance(self.reflection, ast.ClassDef)

    @property
    def is_function(self):
        return isinstance(self.reflection, (ast.FunctionDef, ast.AsyncFunctionDef))

    @property
    def is_async(self):
        return isinstance(self.reflection, ast.AsyncFunctionDef)

    def collect_functions(self, node):
        if isinstance(node, (ast.FunctionDef, ast.FunctionType, ast.AsyncFunctionDef)):
            self._functions.append(ASTObject(node.name, node, self).setup())
            if isinstance(node, ast.FunctionType):
                raise NotImplementedError(f'Function type {type(node).__name__} not implemented yet')
            return node

    def collect_values(self, node):
        if isinstance(node, (ast.TypeVar)):
            return node

    def collect_constants(self, node):
        if isinstance(node, (ast.Constant)):
            return node

    @property
    def classes(self):
        return self._classes

    @property
    def functions(self):
        return [] if self.is_class else self._functions

    # TODO: add generators definitions
    def _collect_generators(self, node):
        from importlib import import_module
        return node

    def __collect_generators(self, node):
        import importlib
        return node

    @property
    def methods(self):
        return self._functions if self.is_class else []

    @property
    def imports(self):
        return self._imports

    @property
    def physical_weight(self):
        return self._end - max(0, self._start - 1)  # csl
    LOC = physical_weight  # The number of source lines

    @property
    def source_weight(self):
        return self.LOC-self.comments-self.spaces # csl
    SLOC = source_weight  # The number of source lines of code

    @property
    def logical_weight(self):
        """ The number of Logical Lines Of Code (LLOC) """
        raw = ast.unparse(self.reflection).splitlines()
        code = [line for line in raw if line.strip()]
        return len(code)
    LLOC = logical_weight # The number of logical lines of code

    # Halstead metrics implementation
    @property
    def _n1(self):
        return self.halstead['n1']

    @property
    def _n2(self):
        return self.halstead['n2']

    @property
    def _N1(self):
        return self.halstead['N1']

    @property
    def _N2(self):
        return self.halstead['N2']

    @property
    def halstead(self):
        cache = getattr(self, '_cache', None)
        if not cache:
            cache = HalsteadVisitor(self.reflection, exclude_docstrings=True, )
        return cache.halstead

    def get_path(self):
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
        if not isinstance(self.reflection, ast.Module):
            if hasattr(self.reflection, 'lineno'):
                return self.reflection.lineno - (self.decorators.LOC if self.is_decorated else 0)
            if hasattr(self.reflection, 'body') and self.reflection.body:
                return type(self)('test', self.reflection.body[0], self)._start
        return 0

    @property
    def is_module(self):
        return isinstance(self.reflection, ast.Module)

    @property
    def spaces(self, response = 0):
        if self.source:
            for line in self.source[max(0, self._start - 1): self._end]:
                response += not len(line.strip())
        return response

    @property
    def comments(self, response = 0):
        if self.source:
            for line in self.source[max(0, self._start - 1): self._end]:
                response += line.strip().startswith('#')
        return response

    @property
    def generators(self):
        """Return list of generator functions"""
        return [func for func in self.functions if func.is_generator]

    @property
    def is_generator(self):
        if self.if_function:
            for child_node in ast.iter_child_nodes(self.reflection):
                if isinstance(child_node, (ast.Yield, ast.YieldFrom)):
                    return True

    def _start_module(self, node):
        if self.collect_modules(node):
            start_node = ast.increment_lineno(ast.fix_missing_locations(ast.Expr('')), -1)
            self.children.insert(0, ASTObject(f'Start Node for {self.name}', start_node, self).setup())
        return self

    @property
    def source(self):
        return self.source_lines or (self.parent and self.parent.source) or []

def init(path, cls=ASTObject):
    path = Path(path)
    source = path.read_text(encoding='utf-8')
    node = ast.parse(source, filename=str(path.absolute()))
    return cls('root', node, path=path, source_lines=source.splitlines())._start_module(node).setup()

if __name__ == '__main__':
    path = Path(__file__)
    root = init(path)
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

    root = init(path)
    print(root._n1, root._n2, root._N1, root._N2)
    print(root.halstead)

