#!/usr/bin/env python3
import ast
import sys
from pathlib import Path


COMPLEXITY_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.AsyncFor,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.IfExp,       # ternary: a if cond else b
)

COMPREHENSION_NODES = (
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def iter_nodes_excluding_functions(node):
    """
    Walk AST depth-first but do NOT descend into nested
    functions, lambdas, or classes. That way each function’s
    complexity is self-contained.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.Lambda, ast.ClassDef)):
            # treat the nested function/class as a leaf
            continue
        yield child
        yield from iter_nodes_excluding_functions(child)


def cyclomatic_complexity(root):
    """
    Basic McCabe cyclomatic complexity for a given AST root:
    CC = 1 + number of decision points.
    """
    complexity = 1  # base path

    for node in iter_nodes_excluding_functions(root):
        # Simple decision / control-flow nodes
        if isinstance(node, COMPLEXITY_NODES):
            complexity += 1

        # Boolean operations (each 'and'/'or' after the first adds a path)
        elif isinstance(node, ast.BoolOp):
            # "a and b and c" => 2 extra decisions
            complexity += max(0, len(node.values) - 1)

        # Each except handler adds a path
        elif isinstance(node, ast.ExceptHandler):
            complexity += 1

        # Comprehensions: each "for" and each "if" inside adds complexity
        elif isinstance(node, COMPREHENSION_NODES):
            for gen in node.generators:
                complexity += 1                # the "for"
                complexity += len(gen.ifs)     # any "if" clauses

        # Assertions carry a condition too
        elif isinstance(node, ast.Assert):
            complexity += 1

    return complexity


def compute_file_complexity(source: str):
    tree = ast.parse(source)

    functions = {}
    # Module-level (top-level) code complexity
    module_complexity = cyclomatic_complexity(tree)

    # Functions & methods
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Build a qualified name for methods: ClassName.method
            qualname = node.name
            parent = getattr(node, "parent", None)
            while parent:
                if isinstance(parent, ast.ClassDef):
                    qualname = f"{parent.name}.{qualname}"
                parent = getattr(parent, "parent", None)

            functions[qualname] = cyclomatic_complexity(node)

    return module_complexity, functions


def attach_parents(tree):
    """
    Convenience: add .parent attributes so we can build qualified names.
    """
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "parent", parent)


def main(path: str):
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    attach_parents(tree)

    module_complexity, functions = compute_file_complexity(source)

    print(f"File: {path}")
    print(f"Module (top-level) cyclomatic complexity: {module_complexity}")
    print()
    print("Per-function cyclomatic complexity:")
    for name, cc in sorted(functions.items()):
        print(f"  {name}: {cc}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {Path(sys.argv[0]).name} <python_file.py>")
        sys.exit(1)
    main(sys.argv[1])
