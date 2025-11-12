"""a set of software metrics developed by Maurice Halstead to measure code complexity based on the number of operators and operands in the source code"""
import math
from collections import Counter
from dataclasses import dataclass, field
import ast
from stats import ASTObject as baseASTObject
from pathlib import Path

transformer = {
    'ast.Add': '+', 'ast.Sub': '-', 'ast.Mult': '*', 'ast.MatMult': '[]*[]',
    'ast.Div': '/', 'ast.FloorDiv': '//', 'ast.Mod': '%', 'ast.Pow': '**',

    'ast.And': 'and', 'ast.Or': 'or', 'ast.Not': 'not',

    'ast.BitAnd': '&', 'ast.BitOr': '|', 'ast.BitXor': '^',
    'ast.LShift': '<<', 'ast.RShift': '>>',

    'ast.UAdd': 'u+', 'ast.USub': 'u-', 'ast.Invert': '~',

    'ast.Eq': '==', 'ast.NotEq': '!=', 'ast.Lt': '<', 'ast.LtE': '<=', 'ast.Gt': '>', 'ast.GtE': '>=',
    'ast.Is': 'is', 'ast.IsNot': 'is not', 'ast.In': 'in', 'ast.NotIn': 'not in',

    'ast.AugAssign.Add': '+=', 'ast.AugAssign.Sub': '-=', 'ast.AugAssign.Mult': '*=', 'ast.AugAssign.MatMult': '[]*[]=',
    'ast.AugAssign.Div': '/=', 'ast.AugAssign.FloorDiv': '//=', 'ast.AugAssign.Mod': '%=', 'ast.AugAssign.Pow': '**=',
    'ast.AugAssign.BitAnd': '&=', 'ast.AugAssign.BitOr': '|=', 'ast.AugAssign.BitXor': '^=',
    'ast.AugAssign.LShift': '<<=', 'ast.AugAssign.RShift': '>>=',
}

@dataclass
class ASTObject(baseASTObject):
    exclude_docstring: bool = True # skip docstring from complexity or not
    operators: Counter[str] = field(default_factory=Counter)  # imported
    operands: Counter[str] = field(default_factory=Counter)

    @property
    def halstead(self):
        if not getattr(self, '_halstead', None):
            # derive metrics from counters
            # for operator in list(self.operators_counter):
            #     if operator in transformer:
            #         self.operators_counter[transformer[operator]] = self.operators_counter.pop(operator)

            if not self.is_docstring:
                self.visit(self.reflection)
                for halstead in [children.halstead for children in self.children]:
                    self.operands.update(halstead['operands'])
                    self.operators.update(halstead['operators'])


            halstead = self._halstead = { 'operands': self.operands, 'operators': self.operators, 'n1': len(self.operators), 'n2': len(self.operands), 'N1': sum(self.operators.values()), 'N2': sum(self.operands.values())}

            n1, n2, N1, N2 = halstead['n1'], halstead['n2'], halstead['N1'], halstead['N2']
            n, N = n1 + n2, N1 + N2
            volume = N * math.log2(n or 1)
            difficulty = n and ((n1 / 2.0) * (N2 / n2)) or 0
            effort = difficulty * volume
            halstead.update(vocabulary = n, length = N, volume = volume, difficulty = difficulty, effort = effort)
        return self._halstead

    def visit(self, node):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        if hasattr(self, method):
            getattr(self, method)(node)
        return self

    # helpers
    def add_op(self, *args):
        self.operators.update(args)

    def add_operand(self, *args):
        self.operands.update(args)

    # Operand visitors
    def visit_Name(self, node: ast.Name):
        self.add_operand(node.id)

    def visit_Constant(self, node: ast.Constant):
        # Constants are operands; docstrings are skipped at parent level
        self.add_operand(f'{node.value}')

    def visit_arg(self, node: ast.arg):
        # Parameter name counts as operand
        if node.arg:
            self.add_operand(node.arg)
        # also visit annotation to capture identifiers/constants used in types
        if node.annotation:
            self.add_op('hint')
            # loop by list of annotations
            self.visit(node.annotation)

    # Structural and definition nodes
    def visit_decorators(self, node):
        if hasattr(node, 'decorator_list'):
            for _decorator in node.decorator_list:
                 self.add_op('@')

    def visit_returns(self, node):
        if hasattr(node, 'returns') and node.returns:
            self.add_op('->')
            # self.visit(node.returns)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.add_op('def')
        self.visit_decorators(node)
        self.visit_returns(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_op('async')
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_op('class')
        self.add_operand(node.name)
        self.visit_decorators(node)
        self.visit_returns(node)


    def visit_Lambda(self, node: ast.Lambda):
        self.add_op('lambda')

    # Imports
    def _count_dotted_name(self, dotted: str):
        if dotted:
            parts = dotted.split('.')
            for i, part in enumerate(parts):
                if part:
                    self.add_operand(part)
                if i < len(parts) - 1:
                    self.add_op('.')

    def visit_Import(self, node: ast.Import):
        self.add_op('import')
        for alias in node.names:
            self._count_dotted_name(alias.name)
            if alias.asname:
                self.add_op('as')
                self.add_operand(alias.asname)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.add_op('from')
        self.add_op('import')
        # leading dots for relative import (level)
        for _ in range(getattr(node, 'level', 0) or 0):
            self.add_op('.')
        self._count_dotted_name(node.module or '')
        for alias in node.names:
            self._count_dotted_name(alias.name)
            if alias.asname:
                self.add_op('as')
                self.add_operand(alias.asname)

    # Expressions and operators
    def visit_BinOp(self, node: ast.BinOp):
        self.add_op(f'ast.{type(node.op).__name__}')

    def visit_BoolOp(self, node: ast.BoolOp):
        sym = f'ast.{type(node.op).__name__}'
        # count occurrences between operands
        for i, v in enumerate(node.values):
            if i > 0:
                self.add_op(sym)

    def visit_Compare(self, node: ast.Compare):
        for op in node.ops:
            self.add_op(f'ast.{type(op).__name__}')

    def visit_UnaryOp(self, node: ast.UnaryOp):
        if isinstance(node.op, (ast.USub, ast.UAdd)) and isinstance(node.operand, ast.Constant):
            self.add_operand(ast.unparse(node))
        else:
            self.add_op(f'ast.{type(node.op).__name__}')

    def visit_AugAssign(self, node: ast.AugAssign):
        self.add_op(f'ast.{type(node).__name__}.{type(node.op).__name__}')

    def visit_Assign(self, node: ast.Assign):
        for _op in node.targets:
            self.add_op('=')

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # count '=' if there is an assigned value
        if node.value:
            self.add_op('=')

    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.add_op(':=')

    def visit_JoinedStr(self, node):
        values = [*node.values]

        for idx, value in enumerate(values):
            values[idx] = '{}'
            if isinstance(value, ast.Constant):
                values[idx] = f'{value.value}'

        self.add_op('f')
        self.add_operand(''.join(values))

    def visit_Call(self, node: ast.Call):
        self.add_op('call')
        for kw in node.keywords:
            if kw.arg:
                self.add_operand(kw.arg)  # count keyword name as operand

    def visit_Attribute(self, node: ast.Attribute):
        self.add_op('.')
        self.add_operand(node.attr)

    def visit_Subscript(self, node: ast.Subscript):
        self.add_op('[]')

    def visit_Slice(self, node: ast.Slice):
        self.add_op('ast.Slice')

    def visit_Index(self, node):  # for older Python; kept for completeness
        pass

    def visit_ExtSlice(self, node: ast.ExtSlice):
        self.add_op('...')

    # Control flow and keywords
    def visit_If(self, node: ast.If):
        self.add_op('if')

    def visit_IfExp(self, node: ast.IfExp):
        self.add_op('if')

    def visit_For(self, node: ast.For):
        self.add_op('for')

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.add_op('async')
        self.visit_For(node)

    def visit_While(self, node: ast.While):
        self.add_op('while')

    def visit_With(self, node: ast.With):
        self.add_op('with')

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.add_op('async')
        self.visit_With(node)

    def visit_withitem(self, node: ast.withitem):
        pass

    def visit_Try(self, node: ast.Try):
        self.add_op('try')
        if node.finalbody:
            self.add_op('finally')

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.add_op('except')
        if node.name and isinstance(node.name, str):
            self.add_operand(node.name)

    def visit_Return(self, node: ast.Return):
        self.add_op('return')

    def visit_Raise(self, node: ast.Raise):
        self.add_op('raise')

    def visit_Yield(self, node: ast.Yield):
        self.add_op('yield')

    def visit_YieldFrom(self, node: ast.YieldFrom):
        self.add_op('yield from')

    def visit_Break(self, node: ast.Break):
        self.add_op('break')

    def visit_Continue(self, node: ast.Continue):
        self.add_op('continue')

    def visit_Pass(self, node: ast.Pass):
        self.add_op('pass')

    def visit_Assert(self, node: ast.Assert):
        self.add_op('assert')

    def visit_Await(self, node: ast.Await):
        self.add_op('await')

    def visit_Global(self, node: ast.Global):
        self.add_op('global')

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self.add_op('nonlocal')
        for n in node.names:
            self.add_operand(n)

    def visit_Delete(self, node: ast.Delete):
        self.add_op('del')

    # Pattern matching (Python 3.10+)
    def visit_Match(self, node: ast.Match):
        self.add_op('match')

    def visit_match_case(self, node: ast.match_case):
        self.add_op('case')

    def visit_MatchAs(self, node: ast.MatchAs):
        if node.name:
            self.add_operand(node.name)

    def visit_comprehension(self, node: ast.comprehension):
        if node.is_async:
            self.add_op('async')
        self.add_op('for')
        for _if in node.ifs:
            self.add_op('if')

    def visit_ListComp(self, node: ast.ListComp):
        self.add_op('ast.listComp')

    def visit_SetComp(self, node: ast.SetComp):
        self.add_op('ast.setComp')

    def visit_DictComp(self, node: ast.DictComp):
        self.add_op('ast.dictComp')

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self.add_op('ast.genExp')

    def visit_Module(self, node: ast.Module):
        # skip mark "self.add_op('ast.module')" because we count into the module, not the module itself
        ...


if __name__ == '__main__':
    path = Path('core1.py')
    root = ASTObject.init(path)
    print('Halstead for:', root.path)
    print(root.halstead)
