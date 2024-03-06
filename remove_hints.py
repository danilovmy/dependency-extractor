import ast
from pathlib import Path
from collections import Counter

SOURCES = Path('legacy_strip_hints/')
REPORTS = Path('logs/')


def parents(path):
    root = Path()
    for directory in path.parts:
        root = root / directory
        if not root.exists():
            root.mkdir()
        if root.is_dir():
            yield root

def initiate(module):
    if module.is_file():
        module = module.parent
    init = module / '__init__.py'
    if not init.exists():
        init.touch()


def base_init(*routes):
    for path in routes:
        for parent in parents(path):
            initiate(parent)
        for module in path.rglob('*.py'):
            for parent in parents(module):
                initiate(parent)

def extract_nodes(filepath):
    for node in ast.walk(ast.parse(filepath.read_text(), filename=filepath.name)):
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Module)):
            yield node

def ast_module_loader(module, collector):
    for node in extract_nodes(module):
        handle_node(node, collector)

def collect_from_node(node, collector):
    node_id = ''
    if isinstance(node, ast.arg):
        node_id = node.arg
    elif isinstance(node, ast.Name):
        node_id = node.id
    elif isinstance(node, ast.Attribute):
        node_id = node.attr
        if hasattr(node, 'slice') and node.slice:
            collect_from_node(node.slice, collector)
        if hasattr(node, 'value') and node.value:
            collect_from_node(node.value, collector)

    elif isinstance(node, ast.Subscript):
        if hasattr(node, 'slice') and node.slice:
            collect_from_node(node.slice, collector)
        if hasattr(node, 'value') and node.value:
            collect_from_node(node.value, collector)
        return
    elif isinstance(node, ast.AnnAssign):
        return collect_from_node(node.annotation, collector)
    else:
        ...

    collector.append((node_id, node.lineno, node.col_offset, node.end_col_offset))

def handle_node(node, collector):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):

        if hasattr(node, 'body') and node.body:
            for part_of_body in node.body:
                handle_node(part_of_body, collector)

        if hasattr(node, 'args') and node.args:
            if isinstance(node.args, ast.arguments):
                arg_node = node.args

                if arg_node.args:
                    for arg in arg_node.args:
                        handle_node(arg, collector)

                if arg_node.kwarg:
                    if not isinstance(arg_node.kwarg, ast.arg):
                        for kwarg in (arg_node.kwarg or []):
                            handle_node(kwarg, collector)

    if hasattr(node, 'annotation') and node.annotation:
        collect_from_node(node.annotation, collector)

    if hasattr(node, 'returns') and node.returns:
        collect_from_node(node.returns, collector)


if __name__ == '__main__':
    base_init(SOURCES, REPORTS)

    type_hints_collector = {}
    for module in SOURCES.rglob('*.py'):
        collector = []
        ast_module_loader(module, collector)
        type_hints_collector[f'{module.absolute()}'] = collector

    report = REPORTS / 'type_hints_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        for name, collector in type_hints_collector.items():
            destination.writelines([f'{len(collector)} {name}\n'])

    report = REPORTS / 'type_hints_variety.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        hints = Counter(hint for value in type_hints_collector.values() for hint, *__ in value)
        for counter, name in hints.most_common():
            destination.writelines([f'{counter} {name}\n'])


    #checker = {'str', 'int', 'bool', 'float', 'Any', 'typing', 'List'}
    #collector = {(node, *collected) for node, *collected in collector if node not in checker}
    print('finished')
    print('summary type hints used:', sum(len(val) for val in type_hints_collector.values()))
    print('summary files with hints:', sum(len(val) and 1 or 0 for val in type_hints_collector.values()))
    print('summary files:', len(type_hints_collector.keys()))
