from collections import Counter
import ast
from pathlib import Path
import importlib

SOURCES = Path('legacy_strip_hints/')
IMPORTS = Path('src/imports/')
REQUIREMENTS = IMPORTS / 'requirements/'
MODULES = Path('src/modules/')
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
    check_requirements(legacy.stem)



def check_requirements(module):

    try:
        importlib.import_module(module)
    except ImportError:
        requirements = REQUIREMENTS / 'requirements.txt'
        if not requirements.exists():
            requirements.touch()

        with requirements.open(mode='r', encoding='utf-8') as source:
            for line in source.readlines():
                if module == line.strip():
                    return

        with requirements.open(mode='a', encoding='utf-8', newline='\n') as destination:
            destination.writelines([f'{module}', '\n'])

def extract_imports(filepath):
    for node in ast.walk(ast.parse(filepath.read_text(), filename=filepath.name)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield type(node).__name__, node

def ast_module_loader(module, collector):

    imports = collector['imported'][str(module)] = collector['imported'].get(str(module)) or {'classes': Counter(), 'modules': Counter()}

    for node_cls, node in extract_imports(module):
        if node_cls == 'ImportFrom':
            collector['imports'].update([node.module])
            imports['modules'].update([node.module])
            for name in node.names:
                imports['classes'].update([f'{name.name} as {name.asname}'] if name.asname else [name.name])
                if collector['imports'][node.module] == 1:
                    check_legacy(f'{node.module}.{name.name}', collector)

        elif node_cls == 'Import':
            for name in node.names:
                collector['imports'].update([name.name])
                imports['modules'].update([name.name])
                imports['classes'].update([f'{name.name} as {name.asname}'] if name.asname else [name.name])
                if collector['imports'][name.name] == 1:
                    check_legacy(f'{name.name}', collector)


if __name__ == '__main__':
    base_init(MODULES, IMPORTS, REQUIREMENTS, SOURCES, REPORTS)

    collector = {
        'imported': {}, # {'filename': {'classes': Counter(), 'modules': Counter()}
        'imports': Counter()
    }

    for module in MODULES.rglob('*.py'):
        ast_module_loader(module, collector)

    report = REPORTS / 'imports_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        for counter, name in collector['imports'].most_common():
            destination.writelines([f'{counter} {name}\n'])

    report = REPORTS / 'classes_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        classes = [(len(val['classes']), key) for key, val in collector['imported'].items()]
        classes.sort(key=lambda val: val[0], reverse = True)
        for (counter, name) in classes:
            destination.writelines([f'{counter} {name}\n'])

    report = REPORTS / 'modules_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        modules = [(len(val['modules']), key) for key, val in collector['imported'].items()]
        modules.sort(key=lambda val: val[0], reverse = True)
        for (counter, name) in modules:
            destination.writelines([f'{counter} {name}\n'])

    print('legacy stats', len((*SOURCES.rglob('*.py'),)))

    counter = len(collector['imports'])
    print('find {} dependencies'.format(counter))
