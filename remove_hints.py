import ast
from collections import Counter
from utils import parser, SOURCES, RESULTS, base_init


def extract_nodes(filepath):
    for node in ast.walk(ast.parse(filepath.read_text(), filename=filepath.name)):
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Module)):
            yield node

def ast_module_loader(module, collector, definitions_counter):
    for node in extract_nodes(module):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions_counter[type(node).__name__].update([(module, node.lineno, node.name)])
        handle_node(node, collector)

def collect_from_node(node, collector):
    node_id = ''
    if isinstance(node, ast.arg):
        node_id = node.arg
    elif isinstance(node, ast.Name):
        node_id = node.id
    elif isinstance(node, ast.Attribute):
        if hasattr(node, 'slice') and node.slice:
            print(node, 'slice in attr')
            collect_from_node(node.slice, collector)

        node_id = node.attr
        if hasattr(node, 'value') and node.value:
            value = node.value
            while not isinstance(value, ast.Name):
                node_id = f'{value.attr}.{node_id}'
                value = value.value
            node_id = f'{value.id}.{node_id}'
        node_id = node_id.strip('.')

    elif isinstance(node, ast.Subscript):
        if hasattr(node, 'slice') and node.slice:
            collect_from_node(node.slice, collector)
        #https://github.com/python/cpython/blob/43a6e4fa4934fcc0cbd83f7f3dc1b23a5f79f24b/Lib/ast.py#L606
        if hasattr(node, 'elts') and node.elts:
            print(node, 'elts in sub')
            for elt in node.elts:
                collect_from_node(elt, collector)

        node_id = ''
        if hasattr(node, 'value') and node.value:
            value = node.value
            while not isinstance(value, ast.Name):
                node_id = f'{value.attr}.{node_id}'
                value = value.value
            node_id = f'{value.id}.{node_id}'
        node_id = node_id.strip('.')
    elif isinstance(node, (ast.Tuple, ast.List)):
        if hasattr(node, 'elts') and node.elts:
            for elt in node.elts:
                collect_from_node(elt, collector)
        return
    elif isinstance(node, ast.AnnAssign):
        return collect_from_node(node.annotation, collector)
    elif isinstance(node, ast.Constant):
        node_id = str(node.value)
    elif isinstance(node, ast.Call):
        node_id = f'Call of {node.func.id}'

    elif isinstance(node, ast.BinOp):
        collect_from_node(node.left, collector)
        collect_from_node(node.right, collector)
        return
    else:
        print(node, 'err')
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

def hints_collector(paths=None):
    base_init(RESULTS)
    paths = paths or [SOURCES]
    base_init(*paths)
    type_hints_collector = {}
    string_counter = {}
    definitions_counter = {"FunctionDef": Counter(), "ClassDef": Counter()}
    filecounter = 0
    for filecounter, module in enumerate((filename for path in paths for filename in ([path] if path.is_file() else path.rglob('*.py'))), start=1):
        collector = []
        ast_module_loader(module, collector, definitions_counter)
        type_hints_collector[f'{module}'] = set(collector)
        string_counter[f'{module}'] = len(module.read_text()), len(module.read_text().splitlines())

    report = RESULTS / 'hints_type_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        counter = 0
        collector = sorted(type_hints_collector.items(), key=lambda val: len(val[1]), reverse=True)
        for name, count in collector:
            if len(count):
                counter += 1
                destination.writelines([f'{len(count)} {name}, {count}\n'])

    report = RESULTS / 'hints_type_variety.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        hints = Counter(hint for value in type_hints_collector.values() for hint, *__ in value)
        for name, count in hints.most_common():
            destination.writelines([f'{count} {name}\n'])

    report = RESULTS / 'hints_file_lengths.txt'
    lines_counter = 0
    with report.open(mode='w', encoding='utf-8') as destination:
        string_counter = sorted(string_counter.items(), key=lambda val: val[1][1], reverse=True)
        for name, (chars, lines) in string_counter:
            if lines:
                lines_counter += lines
                destination.writelines([f'{lines} {name}, chars: {chars}\n'])

    print('summary files for hinting:', filecounter)
    print('summary files with hints:', sum(len(val) and 1 or 0 for val in type_hints_collector.values()))
    print('summary lines of code:', lines_counter)
    print('summary count of classes definitions:', len(definitions_counter["ClassDef"]))
    print('summary count of function definitions:', len(definitions_counter["FunctionDef"]))
    print('summary type hints used:', sum(len(val) for val in type_hints_collector.values()))
    print('hinting finished')

    return type_hints_collector

if __name__ == '__main__':
    init_args = parser.parse_args()
    hints_collector(init_args.filenames)

