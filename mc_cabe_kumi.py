#!/usr/bin/env python3
"""
Pure-standard-library McCabe cyclomatic-complexity counter.
Usage: python mccabe_raw.py file.py
"""

import ast
import sys

# These AST node types each add +1 to complexity
DECISIONS = (
    ast.If, ast.While, ast.For, ast.AsyncFor,
    ast.ExceptHandler,      # every except clause
    ast.With, ast.AsyncWith,
    ast.BoolOp,             # `and` / `or` count once per operator
    ast.ListComp, ast.SetComp, ast.DictComp,
    ast.GeneratorExp, # list/set/dict comprehensions
)

def complexity(node: ast.AST) -> int:
    """Return McCabe complexity for a single function/method node."""
    count = 1  # base path
    for child in ast.walk(node):
        if isinstance(child, DECISIONS):
            # BoolOp: `a and b and c` -> (n-1) operators
            if isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
            else:
                count += 1
    return count

class FuncVisitor(ast.NodeVisitor):
    def __init__(self):
        self.result = []  # [(name, lineno, complexity), ...]

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.result.append((node.name, node.lineno, complexity(node)))
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # treat async def the same

def main(path: str):
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=path)

    visitor = FuncVisitor()
    visitor.visit(tree)

    if not visitor.result:
        print("No functions found.")
        return

    print(f"{'function':<30} {'line':>4}  {'McCabe'}")
    print("-" * 42)
    for name, line, mccabe in visitor.result:
        print(f"{name:<30} {line:>4}  {mccabe:>6}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mccabe_raw.py file.py")
        sys.exit(1)
    main(sys.argv[1])