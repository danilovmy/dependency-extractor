from collections import Counter
import ast
import sys
from pathlib import Path

from utils import parser, SOURCES, RESULTS, base_init

def check_legacy(module, collector):
    module = Path(*module.split('.'))
    legacy = SOURCES / module.parts[0]
    if legacy.exists():
        legacy = SOURCES / module

        if legacy.exists(): # import from module,
            legacy = legacy / '__init__.py'
            return ast_module_loader(legacy, collector)

        legacy = legacy.parent / f'{legacy.stem}.py'
        if legacy.exists(): # import from file
            return ast_module_loader(legacy, collector)

        legacy = legacy.parent.parent / legacy.parent.stem
        if legacy.exists():
            legacy = legacy / '__init__.py'
            return ast_module_loader(legacy, collector)

        legacy = legacy.parent / f'{legacy.stem}.py'
        if legacy.exists():
            return ast_module_loader(legacy, collector)


        raise Exception(f'Legacy module {module} not found')
    check_requirements(legacy.stem, collector)



def check_requirements(module, collector):
    collector['requirements'].update([module])


def extract_imports(filepath):
    for node in ast.walk(ast.parse(filepath.read_text(), filepath.name)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            absolute_path = ''
            if getattr(node, 'level', None):
                absolute_path = '.'.join(filepath.absolute().relative_to(SOURCES.absolute()).parts[0:- node.level])
            yield type(node).__name__, node, absolute_path

def ast_module_loader(module, collector):

    imports = collector['imported'][str(module)] = collector['imported'].get(str(module)) or {'classes': {}, 'modules': Counter()}

    for node_cls, node, absolute_path in extract_imports(module):
        if node_cls == 'ImportFrom':
            node_module = node.module
            if absolute_path:
                node_module = '.'.join((absolute_path, node_module))

            imports['modules'].update([node_module])
            if f'{node_module}'.startswith('importlib'):
                print('importlib detected', module)
            for name in node.names:
                imports['classes'][name.asname if name.asname else name.name] = node_module
                new_module = f'{node_module}.{name.name}'
                collector['imports'].update([new_module])
                if collector['imports'][new_module] == 1:
                    check_legacy(new_module, collector)

        elif node_cls == 'Import':
            for name in node.names:
                node_name = name.name
                if absolute_path:
                    node_name = '.'.join((absolute_path, node_name))
                if f'{node_name}'.startswith('importlib'):
                    print('importlib detected', module)
                collector['imports'].update([node_name])
                imports['modules'].update([node_name])
                imports['classes'][name.asname if name.asname else name.name] = node_name
                if collector['imports'][node_name] == 1:
                    check_legacy(f'{node_name}', collector)

def extract_all_imports(paths=None):
    base_init(RESULTS)
    paths = paths or [SOURCES]
    base_init(*paths)

    collector = {
        'imported': {}, # {'filename': {'classes': dict(), 'modules': Counter()}
        'imports': Counter(),
        'requirements': Counter()
    }

    for module in (filename for path in paths for filename in ([path] if path.is_file() else path.rglob('*.py'))):
        ast_module_loader(module, collector)

    report = RESULTS / 'ast_imports_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        for name, count in collector['imports'].most_common():
            destination.writelines([f'{count} {name}\n'])

    report = RESULTS / 'ast_classes_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        classes = [(len(val['classes']), key) for key, val in collector['imported'].items()]
        classes.sort(key=lambda val: val[0], reverse = True)
        for (counter, name) in classes:
            destination.writelines([f'{counter} {name}, {collector["imported"][name]["classes"].keys()}\n'])

    report = RESULTS / 'ast_modules_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        modules = [(len(val['modules']), key) for key, val in collector['imported'].items()]
        modules.sort(key=lambda val: val[0], reverse = True)
        for (counter, name) in modules:
            destination.writelines([f'{counter} {name}\n'])


    required_modules = set(collector['requirements']).difference((*sys.stdlib_module_names, *sys.builtin_module_names))
    requirements = RESULTS / 'requirements.txt'
    with requirements.open(mode='w', encoding='utf-8', newline='\n') as destination:
        for module in required_modules:
            destination.writelines([f'{module}', '\n'])

    print('find {} dependencies'.format(len(collector['imported'])))
    print('find {} libraries to install'.format(len(required_modules)))
    print('find {} built-in dependencies'.format(len(collector['imports']) - len(required_modules) - len(collector['imported'])))
    print('search of dependencies finished')

    return collector



if __name__ == '__main__':
    init_args = parser.parse_args()
    extract_all_imports(init_args.filenames)