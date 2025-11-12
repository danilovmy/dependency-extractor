#!/usr/bin/env python3
# cognitive_complexity.py - CLI tool
# Usage: python cognitive_complexity.py path/to/file.py

import ast
import sys
from collections import defaultdict, deque
from pathlib import Path

class CognitiveComplexityAnalyzer(ast.NodeVisitor):
    """
    Approximate implementation of SonarSource's Cognitive Complexity for Python.

    Key features implemented (approximate, based on Sonar whitepaper):
      - Structural increments: if, for, while, async for, except handlers
      - Hybrid increments: elif / else (count as increment but no nesting penalty)
      - Nesting: each structural/hybrid construct increases nesting level for nested constructs
      - Boolean operator sequences: add (n_operands - 1) for each BoolOp node
      - Recursion: detects recursion cycles among functions defined in the same AST (SCC)
      - Try/except: each except handler adds +1 (try itself ignored)
      - Lambdas and nested functions: increase nesting when nested
      - Returns do NOT add complexity (per Sonar whitepaper)

    Approximations / limitations:
      - Indirect recursion across modules is not detected (only within the analyzed AST tree)
      - Mixed boolean operators are counted via nested BoolOp nodes (AST structure dependent)
      - 'elif'/'else' handling: implemented as hybrid increments in the visitor
      - Some language-specific constructs are approximated (e.g., match/case)
    """
    def __init__(self):
        super().__init__()
        self.func_complexities = {}
        self._current_func = None
        self._local_complexity = 0
        self._nesting = 0
        self.calls = defaultdict(set)        # caller-qualified-name -> set(callee_simple_names)
        self.func_nodes = {}                 # qualified_name -> ast.FunctionDef
        self._func_stack = []                # stack of function names for qualification

    # --------------- bookkeeping ----------------
    def _enter_function(self, name, node):
        self._func_stack.append(name)
        prev = (self._current_func, self._local_complexity, self._nesting)
        self._current_func = name
        self._local_complexity = 0
        # nested functions start with nesting level 1 per Sonar rules about nested methods
        self._nesting = 0 if len(self._func_stack) == 1 else 1
        return prev

    def _exit_function(self, prev):
        func_name = self._current_func
        self.func_complexities[func_name] = self._local_complexity
        self._current_func, self._local_complexity, self._nesting = prev
        self._func_stack.pop()

    def _struct_incr(self, amount=1):
        """Structural increment: amount + nesting penalty"""
        penalty = self._nesting
        self._local_complexity += amount + penalty

    def _hybrid_incr(self, amount=1):
        """Hybrid increment: increment without nesting penalty"""
        self._local_complexity += amount

    # --------------- AST visitors ----------------
    def visit_Module(self, node):
        # Collect top-level functions first (helps callgraph mapping)
        for n in node.body:
            if isinstance(n, ast.FunctionDef):
                qual = self._qualify_name(n.name)
                self.func_nodes[qual] = n
        # Generic visit to collect calls & compute complexity
        self.generic_visit(node)
        # After traversal, detect recursion cycles and add +1 to participants
        self._apply_recursion_bonus()

    def _qualify_name(self, name):
        if not self._func_stack:
            return name
        return ".".join(self._func_stack + [name])

    def visit_FunctionDef(self, node):
        name = self._qualify_name(node.name)
        self.func_nodes[name] = node
        prev = self._enter_function(name, node)
        # Visit defaults, decorators, body
        for d in node.args.defaults:
            self.visit(d)
        for d in node.decorator_list:
            self.visit(d)
        for stmt in node.body:
            self.visit(stmt)
        self._exit_function(prev)

    def visit_Lambda(self, node):
        # Lambda doesn't get structural increment but acts like nested method: increases nesting temporarily
        old_nesting = self._nesting
        if self._nesting >= 0:
            self._nesting += 1
        self.generic_visit(node)
        self._nesting = old_nesting

    def visit_If(self, node):
        # 'if' is structural: +1 + nesting penalty
        self._struct_incr(1)
        # Visit body with nesting increased
        self._nesting += 1
        for stmt in node.body:
            self.visit(stmt)
        self._nesting -= 1

        # Handle orelse: elif chains or else branch are hybrid increments and increase nesting for their bodies
        orelse = node.orelse
        if orelse:
            current = orelse
            while current:
                if len(current) == 1 and isinstance(current[0], ast.If):
                    # 'elif' as If in orelse: hybrid increment (+1), body gets nesting+1
                    self._hybrid_incr(1)
                    self._nesting += 1
                    for stmt in current[0].body:
                        self.visit(stmt)
                    self._nesting -= 1
                    current = current[0].orelse
                else:
                    # else branch (not an 'elif')
                    self._hybrid_incr(1)
                    self._nesting += 1
                    for stmt in current:
                        self.visit(stmt)
                    self._nesting -= 1
                    break

    def visit_For(self, node):
        self._struct_incr(1)
        self._nesting += 1
        self.visit(node.target)
        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)
        self._nesting -= 1
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def visit_While(self, node):
        self._struct_incr(1)
        self._nesting += 1
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        self._nesting -= 1
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_Try(self, node):
        # try itself ignored; each except handler is structural (+1) and its body is nested
        for stmt in node.body:
            self.visit(stmt)
        for handler in node.handlers:
            self._struct_incr(1)
            self._nesting += 1
            for stmt in handler.body:
                self.visit(stmt)
            self._nesting -= 1
        for stmt in node.orelse:
            self.visit(stmt)
        for stmt in node.finalbody:
            self.visit(stmt)

    def visit_BoolOp(self, node):
        # For N operands, N-1 binary ops -> add N-1
        n_operands = len(node.values)
        if n_operands > 1:
            self._local_complexity += (n_operands - 1)
        for v in node.values:
            self.visit(v)

    def visit_Compare(self, node):
        self.generic_visit(node)

    def visit_Call(self, node):
        callee = None
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr
        if callee and self._current_func is not None:
            self.calls[self._current_func].add(callee)
        self.generic_visit(node)

    def visit_Return(self, node):
        # Sonar: early return doesn't add complexity. Still visit value.
        if node.value:
            self.visit(node.value)

    def visit_Break(self, node):
        return

    def visit_Continue(self, node):
        return

    def visit_Raise(self, node):
        self.generic_visit(node)

    def generic_visit(self, node):
        super().generic_visit(node)

    # ---------- Recursion detection ----------
    def _apply_recursion_bonus(self):
        # Build call graph among qualified functions known in func_nodes.
        # Map simple name -> list of qualified names
        name_to_quals = defaultdict(list)
        for qual in self.func_nodes.keys():
            simple = qual.split('.')[-1]
            name_to_quals[simple].append(qual)
        graph = {qual: set() for qual in self.func_nodes.keys()}
        for caller_qual, callees in self.calls.items():
            # caller_qual might be qualified or simple, match graph keys ending with it
            matching_callers = [k for k in graph.keys() if k.endswith(caller_qual)]
            if not matching_callers:
                continue
            for caller in matching_callers:
                for callee_simple in callees:
                    targets = name_to_quals.get(callee_simple, [])
                    for t in targets:
                        graph[caller].add(t)
        # Tarjan's algorithm for SCCs
        index = 0
        indices = {}
        lowlink = {}
        stack = []
        onstack = set()
        sccs = []

        def strongconnect(v):
            nonlocal index
            indices[v] = index
            lowlink[v] = index
            index += 1
            stack.append(v)
            onstack.add(v)
            for w in graph.get(v, ()):
                if w not in indices:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif w in onstack:
                    lowlink[v] = min(lowlink[v], indices[w])
            if lowlink[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    onstack.remove(w)
                    scc.append(w)
                    if w == v:
                        break
                sccs.append(scc)

        for v in graph.keys():
            if v not in indices:
                strongconnect(v)

        # Add +1 complexity to any function in an SCC size>1 or with self-loop
        for scc in sccs:
            if len(scc) > 1:
                for fn in scc:
                    self.func_complexities[fn] = self.func_complexities.get(fn, 0) + 1
            else:
                v = scc[0]
                if v in graph and v in graph[v]:
                    self.func_complexities[v] = self.func_complexities.get(v, 0) + 1

def analyze_source(source: str):
    tree = ast.parse(source)
    analyzer = CognitiveComplexityAnalyzer()
    analyzer.visit(tree)
    total = sum(analyzer.func_complexities.values())
    return analyzer.func_complexities, total

# CLI behavior
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(prog='cognitive_complexity.py', description='Compute Cognitive Complexity (Sonar-like) for Python files.')
    parser.add_argument('paths', nargs='+', help='Python file(s) or directories to analyze.')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recurse into directories.')
    args = parser.parse_args(argv)

    files = []
    for p in args.paths:
        p = Path(p)
        if p.is_file() and p.suffix == '.py':
            files.append(p)
        elif p.is_dir() and args.recursive:
            files.extend([f for f in p.rglob('*.py')])
        elif p.is_dir():
            files.extend([f for f in p.iterdir() if f.is_file() and f.suffix == '.py'])

    grand_total = 0
    per_file = {}
    for f in files:
        try:
            src = f.read_text(encoding='utf8')
        except Exception as e:
            print(f"Could not read {f}: {e}", file=sys.stderr)
            continue
        func_map, total = analyze_source(src)
        per_file[str(f)] = {'total': total, 'functions': func_map}
        grand_total += total

    for fname, data in per_file.items():
        print(f'File: {fname}  Total cognitive complexity: {data["total"]}')
        for func, c in data['functions'].items():
            print(f'  {func}: {c}')
    print(f'Grand total: {grand_total}')

if __name__ == '__main__':
    main()
