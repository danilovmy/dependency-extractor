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
