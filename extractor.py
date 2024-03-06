import importlib
import ast
from pathlib import Path
import sys
from unittest.mock import Mock

SOURCES = Path('legacy_strip_hints/')
IMPORTS = Path('src/imports/')
REQUIREMENTS = IMPORTS / 'requirements/'
MODULES = Path('src/modules/')
FAKE = Path('fake/')

sys.path.append(str(FAKE.absolute()))

def parents(path):
    root = Path()
    for directory in path.parts:
        root = root / directory
        if not root.exists():
            root.mkdir()
        if root.is_dir():
            yield root

def initiate(module, source=None):
    if module.is_file():
        module = module.parent

    init = module / '__init__.py'

    if not init.exists():
        init.touch()

    if source:
        init.write_text(source.read_text())


def base_init(*routes):
    for path in routes:
        for parent in parents(path):
            initiate(parent)
        for module in path.rglob('*.py'):
            for parent in parents(module):
                initiate(parent)

# def check_legacy(module):
#     legacy = SOURCES / module.split('.')[0]
#     if legacy.exists():
#         legacy = SOURCES / module.replace('.', '/')
#         if legacy.exists():
#             sys.modules[module] = Mock()
#             return True

#         legacy = legacy.parent / f'{legacy.name}.py'
#         if legacy.exists():
#             imports = IMPORTS / f'{module.replace(".", "_")}.py'
#             if not imports.exists():
#                 imports.write_text(legacy.read_text())

#             sys.modules[module] = Mock()
#             module_loader(imports)
#             return True

#         raise Exception(f'Legacy module {module} not found')

def check_legacy(module):
    legacy = SOURCES / module.split('.')[0]

    if legacy.exists():
        legacy = SOURCES / module.replace('.', '/')
        faker = FAKE / module.replace('.', '/')
        for __ in parents(faker.parent):
            pass
        if legacy.exists():
            if not faker.exists():
                faker.mkdir()
            print(faker)
            return True

        legacy = legacy.parent / f'{legacy.name}.py'
        faker = faker.parent / f'{faker.name}.py'
        if legacy.exists():
            if not faker.exists():
                faker.write_text(legacy.read_text())
            module_loader(faker)
            print(faker)
            return True

        legacy = legacy.parent / '__init__.py'
        faker = faker.parent / '__init__.py'
        if legacy.exists():
            faker.write_text(legacy.read_text())
            module_loader(faker)

        raise Exception(f'Legacy module {module} not found')



def check_requirements(module):
    sys.modules[module] = Mock()
    requirements = REQUIREMENTS / 'requirements.txt'
    if not requirements.exists():
        requirements.touch()
    module, _splitter, _last = module.partition('.')
    with requirements.open(mode='r', encoding='utf-8') as source:
        for line in source.readlines():
            if module == line.strip():
                return

    with requirements.open(mode='a', encoding='utf-8', newline='\n') as destination:
        destination.writelines([f'{module}', '\n'])

def extract_imports(filepath):
    for node in ast.walk(ast.parse(filepath.read_text(), filename=filepath.name)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            yield node

def ast_module_loader(module):
    for node in extract_imports(module):
        print(type(node).__name__, getattr(node, 'module', None), [(name.name, name.asname) for name in node.names])

def module_loader(module):
    success = False
    counter = 0

    while not success:
        try:
            if module.name != '__init__.py':
                importlib.import_module('.'.join(module.parts))
            success = True
        except ImportError as error:
            print(error, module)
            counter += 1
            if not check_legacy(error.name):
                check_requirements(error.name)
        except TypeError as error:
            print(error, module)
            # if "'Mock'" not in str(error) and "metaclass conflict" not in str(error):
            #     raise TypeError from error
            success = True
        except AttributeError as error:
            print(error, module)
            # if 'Mock object' in str(error):
            #print(error)
            #     raise AttributeError from error
            success = True
        except KeyError as error:
            print(error, module)
            success = True
        except Exception as error:
            raise Exception(f'Can not continue due error {error}') from error

    return counter


if __name__ == '__main__':
    sys.path.insert(0, str(FAKE.absolute()))

    base_init(MODULES, FAKE, IMPORTS, REQUIREMENTS, MODULES)
    print('legacy stats', len([file for file in SOURCES.rglob('*.py')]))

    for module in MODULES.rglob('*.py'):
        # module_loader(module)
        ast_module_loader(module)

    counter = len(list(FAKE.rglob('*.py')))

    sys.path.remove(str(FAKE.absolute()))
    print('find {} dependencies'.format(counter))
