import math
from collections import Counter
import ast
class HalsteadVisitor(ast.NodeVisitor):
    def __init__(self, node, exclude_docstrings = True):
        self.reflection = node
        self.exclude_docstrings = exclude_docstrings
        self.operators_counter: Counter[str] = Counter()
        self.operands_counter: Counter[str] = Counter()

    @property
    def halstead(self):
        cache = getattr(self, '_cache', None)
        if not cache:
            self.visit(self.reflection)
            # derive metrics from counters
            operators = list(self.operators_counter)
            operands = list(self.operands_counter)
            cache = self._cache = { 'operands': operands, 'operators': operators, 'n1': len(operators), 'n2': len(operands), 'N1': sum(self.operators_counter.values()), 'N2': sum(self.operands_counter.values())}
            n1, n2, N1, N2 = cache['n1'], cache['n2'], cache['N1'], cache['N2']
            n, N = n1 + n2, N1 + N2
            volume = N * math.log2(n or 1)
            difficulty = n and ((n1 / 2.0) * (N2 / n2)) or 0
            effort = difficulty * volume
            cache.update(vocabulary = n, length = N, volume = volume, difficulty = difficulty, effort = effort)
        return cache

    # helpers
    def add_op(self, *args):
        self.operators_counter.update(args)

    def add_operand(self, *args):
        self.operands_counter.update(args)

    # utilities for operators
    @staticmethod
    def _binop_symbol(op):
        return {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.MatMult: '@',
            ast.Div: '/', ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**',
            ast.BitAnd: '&', ast.BitOr: '|', ast.BitXor: '^',
            ast.LShift: '<<', ast.RShift: '>>',
        }.get(type(op), type(op).__name__)

    @staticmethod
    def _unary_symbol(op):
        return {ast.UAdd: 'u+', ast.USub: 'u-', ast.Not: 'not', ast.Invert: '~'}.get(type(op), type(op).__name__)

    @staticmethod
    def _boolop_symbol(op):
        return {ast.And: 'and', ast.Or: 'or'}.get(type(op), type(op).__name__)

    @staticmethod
    def _cmpop_symbol(op):
        return {
            ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>=',
            ast.Is: 'is', ast.IsNot: 'is not', ast.In: 'in', ast.NotIn: 'not in'
        }.get(type(op), type(op).__name__)

    @classmethod
    def _aug_symbol(cls, op):
        base = cls._binop_symbol(op)
        # map back from '+' etc to '+=' style where possible
        mapping = {
            '+': '+=', '-': '-=', '*': '*=', '@': '@=', '/': '/=', '//': '//=', '%': '%=', '**': '**=',
            '&': '&=', '|': '|=', '^': '^=', '<<': '<<=', '>>': '>>='
        }
        return mapping.get(base, f'aug_{base}')

    def _visit_body_skipping_docstring(self, body):
        if not isinstance(body, list):
            return
        start = 1 if (self.exclude_docstrings and body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) and isinstance(body[0].value.value, str)) else 0
        for stmt in body[start:]:
            self.visit(stmt)

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
            self.visit(node.annotation)

    # Structural and definition nodes
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.add_op('def')
        # parameters
        for a in list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs):
            self.visit(a)
        if node.args.vararg:
            self.visit(node.args.vararg)
        if node.args.kwarg:
            self.visit(node.args.kwarg)
        # defaults and annotations
        for d in list(getattr(node.args, 'defaults', [])) + list(getattr(node.args, 'kw_defaults', [])):
            if d is not None:
                self.visit(d)
        for dec in node.decorator_list:
            self.visit(dec)
        for b in node.returns,:
            if b:
                self.visit(b)
        # skip docstring
        self._visit_body_skipping_docstring(node.body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.add_op('async')
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.add_op('class')
        for b in node.bases:
            self.visit(b)
        for kw in node.keywords:
            self.visit(kw)
        for dec in node.decorator_list:
            self.visit(dec)
        self._visit_body_skipping_docstring(node.body)

    def visit_Lambda(self, node: ast.Lambda):
        self.add_op('lambda')
        # parameters
        for a in list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs):
            self.visit(a)
        if node.args.vararg:
            self.visit(node.args.vararg)
        if node.args.kwarg:
            self.visit(node.args.kwarg)
        self.visit(node.body)

    # Imports
    def _count_dotted_name(self, dotted: str):
        if not dotted:
            return
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
        self.add_op(self._binop_symbol(node.op))
        self.visit(node.left)
        self.visit(node.right)

    def visit_BoolOp(self, node: ast.BoolOp):
        sym = self._boolop_symbol(node.op)
        # count occurrences between operands
        for i, v in enumerate(node.values):
            if i > 0:
                self.add_op(sym)
            self.visit(v)

    def visit_Compare(self, node: ast.Compare):
        self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            self.add_op(self._cmpop_symbol(op))
            self.visit(comp)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        if isinstance(node.op, (ast.USub, ast.UAdd)) and isinstance(node.operand, ast.Constant):
            self.add_operand(ast.unparse(node))
        else:
            self.add_op(self._unary_symbol(node.op))
            self.visit(node.operand)

    def visit_AugAssign(self, node: ast.AugAssign):
        self.add_op(self._aug_symbol(node.op))
        self.visit(node.target)
        self.visit(node.value)

    def visit_Assign(self, node: ast.Assign):
        # '=' once per target in chain assignment
        self.add_op('=')
        for _ in node.targets[1:]:
            self.add_op('=')
        for t in node.targets:
            self.visit(t)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # count '=' if there is an assigned value
        if node.value is not None:
            self.add_op('=')
            self.visit(node.value)
        self.visit(node.annotation)
        self.visit(node.target)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        self.add_op(':=')
        self.visit(node.target)
        self.visit(node.value)

    def visit_JoinedStr(self, node):
        values = [*node.values]
        for idx, value in enumerate(values):
            if isinstance(value, ast.Constant):
                values[idx] = f'{value.value}'
            else:
                self.visit(value)
                values[idx] = '{}'
        self.add_op('f')
        self.add_operand(''.join(values))

    def visit_Call(self, node: ast.Call):
        self.add_op('call')
        self.visit(node.func)
        for a in node.args:
            self.visit(a)
        for kw in node.keywords:
            if kw.arg is not None:
                self.add_operand(kw.arg)  # count keyword name as operand
            if kw.value is not None:
                self.visit(kw.value)

    def visit_Attribute(self, node: ast.Attribute):
        self.add_op('.')
        self.add_operand(node.attr)
        self.visit(node.value)

    def visit_Subscript(self, node: ast.Subscript):
        self.add_op('[]')
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Slice(self, node: ast.Slice):
        if node.lower:
            self.visit(node.lower)
        if node.upper:
            self.visit(node.upper)
        if node.step:
            self.visit(node.step)

    def visit_Index(self, node):  # for older Python; kept for completeness
        self.visit(node.value)

    def visit_ExtSlice(self, node: ast.ExtSlice):
        for d in node.dims:
            self.visit(d)

    # Control flow and keywords
    def visit_If(self, node: ast.If):
        self.add_op('if')
        self.visit(node.test)
        self._visit_body_skipping_docstring(node.body)
        self._visit_body_skipping_docstring(node.orelse)

    def visit_IfExp(self, node: ast.IfExp):
        self.add_op('if')
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_For(self, node: ast.For):
        self.add_op('for')
        self.visit(node.target)
        self.visit(node.iter)
        self._visit_body_skipping_docstring(node.body)
        self._visit_body_skipping_docstring(node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self.add_op('async')
        self.visit_For(node)

    def visit_While(self, node: ast.While):
        self.add_op('while')
        self.visit(node.test)
        self._visit_body_skipping_docstring(node.body)
        self._visit_body_skipping_docstring(node.orelse)

    def visit_With(self, node: ast.With):
        self.add_op('with')
        for item in node.items:
            self.visit(item)
        self._visit_body_skipping_docstring(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.add_op('async')
        self.visit_With(node)

    def visit_withitem(self, node: ast.withitem):
        self.visit(node.context_expr)
        if node.optional_vars:
            self.visit(node.optional_vars)

    def visit_Try(self, node: ast.Try):
        self.add_op('try')
        self._visit_body_skipping_docstring(node.body)
        for h in node.handlers:
            self.visit(h)
        self._visit_body_skipping_docstring(node.orelse)
        if node.finalbody:
            self.add_op('finally')
            self._visit_body_skipping_docstring(node.finalbody)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.add_op('except')
        if node.type:
            self.visit(node.type)
        if node.name:
            # name can be str in older versions; treat as operand
            if isinstance(node.name, str):
                self.add_operand(node.name)
            else:
                self.visit(node.name)
        self._visit_body_skipping_docstring(node.body)

    def visit_Return(self, node: ast.Return):
        self.add_op('return')
        if node.value:
            self.visit(node.value)

    def visit_Raise(self, node: ast.Raise):
        self.add_op('raise')
        if node.exc:
            self.visit(node.exc)
        if node.cause:
            self.visit(node.cause)

    def visit_Yield(self, node: ast.Yield):
        self.add_op('yield')
        if node.value:
            self.visit(node.value)

    def visit_YieldFrom(self, node: ast.YieldFrom):
        self.add_op('yield from')
        self.visit(node.value)

    def visit_Break(self, node: ast.Break):
        self.add_op('break')

    def visit_Continue(self, node: ast.Continue):
        self.add_op('continue')

    def visit_Pass(self, node: ast.Pass):
        self.add_op('pass')

    def visit_Assert(self, node: ast.Assert):
        self.add_op('assert')
        self.visit(node.test)
        if node.msg:
            self.visit(node.msg)

    def visit_Await(self, node: ast.Await):
        self.add_op('await')
        self.visit(node.value)

    def visit_Global(self, node: ast.Global):
        self.add_op('global')
        for n in node.names:
            self.add_operand(n)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self.add_op('nonlocal')
        for n in node.names:
            self.add_operand(n)

    def visit_Delete(self, node: ast.Delete):
        self.add_op('del')
        for t in node.targets:
            self.visit(t)

    # Pattern matching (Python 3.10+)
    def visit_Match(self, node: ast.Match):
        self.add_op('match')
        self.visit(node.subject)
        for c in node.cases:
            self.visit(c)

    def visit_match_case(self, node: ast.match_case):
        self.add_op('case')
        self.visit(node.pattern)
        if node.guard:
            self.visit(node.guard)
        self._visit_body_skipping_docstring(node.body)

    def visit_MatchAs(self, node: ast.MatchAs):
        if node.name:
            self.add_operand(node.name)
        if node.pattern:
            self.visit(node.pattern)

    def visit_comprehension(self, node: ast.comprehension):
        if node.is_async:
            self.add_op('async')
        self.add_op('for')
        self.visit(node.target)
        self.visit(node.iter)
        for if_ in node.ifs:
            self.add_op('if')
            self.visit(if_)

    def visit_ListComp(self, node: ast.ListComp):
        self.visit(node.elt)
        for gen in node.generators:
            self.visit(gen)

    def visit_SetComp(self, node: ast.SetComp):
        self.visit(node.elt)
        for gen in node.generators:
            self.visit(gen)

    def visit_DictComp(self, node: ast.DictComp):
        self.visit(node.key)
        self.visit(node.value)
        for gen in node.generators:
            self.visit(gen)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        self.visit(node.elt)
        for gen in node.generators:
            self.visit(gen)

    # Module/Root
    def visit_Module(self, node: ast.Module):
        self._visit_body_skipping_docstring(node.body)