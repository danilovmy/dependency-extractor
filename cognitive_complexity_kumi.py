# generated from kumi
import ast
import sys
from typing import Dict

class CognitiveComplexityVisitor(ast.NodeVisitor):
    """
    Вычисляет Cognitive Complexity для Python функций на основе правил SonarSource [^31^][^38^].

    Правила:
    1. Игнорировать shorthand: list/set/dict comprehensions, generator expressions, lambda
    2. +1 + уровень_вложенности за каждый разрыв линейного потока:
       - if, for, while, try, with, match, case
       - except, тernary operator (if expr), логические операторы (and/or)
       - рекурсивные вызовы
    3. elif: +1 (без увеличения вложенности)
    4. else, finally: не увеличивают сложность
    """

    def __init__(self):
        self.function_complexities = {}  # имя функции -> сложность
        self.current_function = None
        self.nesting_level = 0
        self.nesting_stack = []
        self.in_shorthand = 0
        self.current_function_name = None

    def _is_shorthand_context(self) -> bool:
        return self.in_shorthand > 0

    def _increment_complexity(self, increment: int):
        if self.current_function:
            self.function_complexities[self.current_function] += increment

    # === Функции ===
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node.name, node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node.name, node)

    def _analyze_function(self, name: str, node: ast.AST):
        old_function = self.current_function
        old_function_name = self.current_function_name
        old_nesting = self.nesting_level

        self.current_function = name
        self.current_function_name = name
        self.function_complexities[name] = 0

        self.nesting_level = 0
        self.nesting_stack = []

        self.generic_visit(node)

        self.current_function = old_function
        self.current_function_name = old_function_name
        self.nesting_level = old_nesting

    # === Shorthand структуры (игнорируем) ===
    def visit_ListComp(self, node: ast.ListComp):
        old_shorthand = self.in_shorthand
        self.in_shorthand += 1
        self.generic_visit(node)
        self.in_shorthand = old_shorthand

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp
    visit_Lambda = visit_ListComp

    # === Управляющие структуры ===
    def visit_If(self, node: ast.If):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        is_elif = getattr(node, '_is_elif', False)

        if is_elif:
            self._increment_complexity(1)
            self.visit(node.test)
            for stmt in node.body:
                self.visit(stmt)
            if node.orelse:
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    node.orelse[0]._is_elif = True
                for stmt in node.orelse:
                    self.visit(stmt)
        else:
            self._increment_complexity(1 + self.nesting_level)
            self.nesting_level += 1
            self.nesting_stack.append('if')

            self.visit(node.test)
            for stmt in node.body:
                self.visit(stmt)

            self.nesting_level -= 1
            self.nesting_stack.pop()

            if node.orelse:
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    node.orelse[0]._is_elif = True
                for stmt in node.orelse:
                    self.visit(stmt)

    def visit_For(self, node: ast.For):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)
        self.nesting_level += 1
        self.nesting_stack.append('for')

        for stmt in node.body:
            self.visit(stmt)

        self.nesting_level -= 1
        self.nesting_stack.pop()

        for stmt in node.orelse:
            self.visit(stmt)

    visit_AsyncFor = visit_For

    def visit_While(self, node: ast.While):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)
        self.nesting_level += 1
        self.nesting_stack.append('while')

        for stmt in node.body:
            self.visit(stmt)

        self.nesting_level -= 1
        self.nesting_stack.pop()

        for stmt in node.orelse:
            self.visit(stmt)

    def visit_With(self, node: ast.With):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)
        self.nesting_level += 1
        self.nesting_stack.append('with')

        for stmt in node.body:
            self.visit(stmt)

        self.nesting_level -= 1
        self.nesting_stack.pop()

    visit_AsyncWith = visit_With

    def visit_Try(self, node: ast.Try):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)

        for stmt in node.body:
            self.visit(stmt)

        for handler in node.handlers:
            self.visit(handler)

        for stmt in node.orelse:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)

        for stmt in node.body:
            self.visit(stmt)

    def visit_Match(self, node: ast.Match):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)

        for case in node.cases:
            self.visit(case)

    def visit_match_case(self, node: ast.match_case):
        if self._is_shorthand_context():
            self.generic_visit(node)
            return

        self._increment_complexity(1 + self.nesting_level)

        for stmt in node.body:
            self.visit(stmt)

    def visit_IfExp(self, node: ast.IfExp):
        if self._is_shorthand_context():
            return

        self._increment_complexity(1 + self.nesting_level)

        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_BoolOp(self, node: ast.BoolOp):
        if self._is_shorthand_context():
            return

        num_operators = len(node.values) - 1

        for i in range(num_operators):
            self._increment_complexity(1 + self.nesting_level)

        for value in node.values:
            self.visit(value)

    def visit_Call(self, node: ast.Call):
        if (self.current_function_name and
            isinstance(node.func, ast.Name) and
            node.func.id == self.current_function_name):
            if not self._is_shorthand_context():
                self._increment_complexity(1 + self.nesting_level)

        self.generic_visit(node)

def analyze_file(filename: str) -> Dict[str, int]:
    """Анализирует Python файл и возвращает сложность функций"""
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        tree = ast.parse(code, filename=filename)
    except SyntaxError as e:
        raise SyntaxError(f"Invalid Python syntax in '{filename}': {e}")

    visitor = CognitiveComplexityVisitor()
    visitor.visit(tree)

    return visitor.function_complexities

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <python_file.py>")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        complexities = analyze_file(filename)

        print(f"Cognitive Complexity Analysis for {filename}")
        print("=" * 60)

        if not complexities:
            print("No functions found.")
            return

        sorted_funcs = sorted(complexities.items(), key=lambda x: x[1], reverse=True)

        total_complexity = 0
        max_name_length = max(len(name) for name in complexities.keys())

        for func_name, complexity in sorted_funcs:
            status = "✓ PASS" if complexity <= 15 else "✗ FAIL"
            print(f"{func_name:.<{max_name_length}} {complexity:>3} {status}")
            total_complexity += complexity

        print("=" * 60)
        print(f"Total functions analyzed: {len(complexities)}")
        print(f"Average complexity: {total_complexity / len(complexities):.1f}")
        print(f"Total file complexity: {total_complexity}")
        print("-" * 60)
        print("Threshold: 15 (SonarCloud default for Python) [^40^]")
        print("Specification: https://www.sonarsource.com/resources/cognitive-complexity/")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except SyntaxError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()