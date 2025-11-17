from collections import Counter
from dataclasses import dataclass, field

import ast

from base import ASTObject as baseASTObject, main
counter = []

@dataclass
class ASTObject(baseASTObject):
    """
    Base wrapper for AST Node
    for complexity measurements
    """
    PIPELINE = 'collect_modules', 'collect_imports', 'collect_classes', 'collect_functions', 'collect_constants', 'collect_values'

    importlib: bool = False  # if importlib used in this reflection
    _attributes: dict = None  # declared attributes
    _constants: dict = None  # declared constants
    _properties: dict = None # declared properties
    _imports: list = field(default_factory=list)  # import statements
    _imported: list = field(default_factory=list)  # imported objects
    _classes: list = field(default_factory=list)
    _functions: list = field(default_factory=list)

    @property
    def have_internals(self):
        """ if declared functions or classes internal """
        if self.is_function and bool(len(self.classes) + len(self.functions)):
            return True
        return any(child.have_internals for child in self.children)

    @property
    def is_docstring(self):
        docstring = self.parent and self.parent.is_docstring
        if docstring:
            return docstring
        if self.is_expr and isinstance(self.reflection.value, ast.Constant) and isinstance(self.reflection.value.value, str) and self.reflection.value  and self.parent and hasattr(self.parent.reflection, 'body') and self.parent.reflection.body:
            return self.reflection is self.parent.reflection.body[0] and self.reflection.value.value

    @property
    def is_expr(self):
        return isinstance(self.reflection, ast.Expr)

    @property
    def have_imports(self):
        """ if declared functions or classes internal """
        return len(self._imports) or any(child.have_imports for child in self.children)

    @property
    def imports(self):
        """ return all imports """
        return *self._imports, *[child.imports for child in self.children if child.imports]

    def collect_modules(self, node):
        if isinstance(node, (ast.Module)):
            return node

    def collect(self, node):
        global counter
        node = super().collect(node) # transform in ASTObject
        any(getattr(self, pipe)(node) for pipe in self.PIPELINE)
        counter += [node.reflection]
        return node

    @property
    def is_import(self):
        return isinstance(self.reflection, (ast.Import, ast.ImportFrom))

    @property
    def imported(self):
        if not self._imported:
            for node in self.imports:
                self._imported += [name.name for name in node.reflection.names]
        return self._imported

    def collect_imports(self, node):
        if node.is_import:
            self._imports.append(node)
            node = node.reflection
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
    @property
    def has_importlib(self):
        return self.importlib or any(child.has_importlib for child in self.children)

    @property
    def is_class(self):
        return isinstance(self.reflection, ast.ClassDef)

    @property
    def is_function(self):
        return isinstance(self.reflection, (ast.FunctionDef, ast.AsyncFunctionDef))

    @property
    def is_async(self):
        return isinstance(self.reflection, ast.AsyncFunctionDef)

    def collect_classes(self, node):
        if node.is_class:
            self._classes.append(node)
            return node

    def collect_functions(self, node):
        if node.is_function:
            self._functions.append(node)
            if isinstance(node.reflection, ast.FunctionType):
                raise NotImplementedError(f'Function type {type(node).__name__} not implemented yet')
            return node

    def collect_values(self, node):
        if isinstance(self.reflection, (ast.TypeVar)):
            return node

    def collect_constants(self, node):
        if isinstance(self.reflection, (ast.Constant)):
            return node

    @property
    def classes(self):
        return self._classes

    @property
    def functions(self):
        return [] if self.is_class else self._functions

    # TODO: add generators definitions
    def collect_generators(self, node):
        if isinstance(node.reflection, (ast.Generator, ast.GeneratorExp)):
            return node

    @property
    def methods(self):
        return self._functions if self.is_class else []

    @property
    def is_module(self):
        return isinstance(self.reflection, ast.Module)

    @property
    def generators(self):
        """Return list of generator functions"""
        return [func for func in self.functions if func.is_generator]

    @property
    def is_generator(self):
        if self.is_function:
            for child_node in ast.iter_child_nodes(self.reflection):
                if isinstance(child_node, (ast.Yield, ast.YieldFrom)):
                    return True

if __name__ == '__main__':
    objects= main(ASTObject)

    imported = Counter()
    imports = Counter()
    imported_objects = Counter()
    for obj in objects:
        imports.update({str(obj.path): len(obj.imports)})

        imported_objects.update({str(obj.path): len(obj.imported)})
        imported.update(obj.imported)

    print('max import lines:', imports.most_common(5))
    print('max imported objects:', imported_objects.most_common(5))
    print('mostly imported:', imported.most_common(5))

    # if root.classes:
    #     cls =root.classes[0]
    #     if cls.children:
    #         child = cls.children[1]
    #         print(child.is_docstring)
    #         print(child.raw_lines)
    #         print(ast.unparse(child.reflection))

    # print('collected', counter)
    # counter = []
    # for child in ast.walk(root.reflection):
    #     counter += [child]

    # print('walked', counter)
