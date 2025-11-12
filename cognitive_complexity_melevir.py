import ast
from pathlib import Path
from cognitive_complexity.api import get_cognitive_complexity


class CognitiveComplexityAnalyzer(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(node.name, get_cognitive_complexity(node))

    def visit_asyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)


if __name__ == '__main__':
    path = Path('cognitive.py')
    tree = ast.parse(path.read_text(encoding='utf-8'))
    CognitiveComplexityAnalyzer().visit(tree)

# _enter_function        │ 1          │
# _enter_function: 0

# _qualify_name          │ 2          │
# _qualify_name: 1

# cognitive_complexity   │ 7          │
# cognitive_complexity: 6
