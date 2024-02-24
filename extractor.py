import importlib
from pathlib import Path
import sys
from unittest.mock import Mock

SOURCES = Path('legacy_strip_hints/')
IMPORTS = Path('src/imports/')
REQUIREMENTS = IMPORTS / 'requirements/'
MODULES = Path('src/modules/')


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
        print('initiate', module)
        init.touch()

def base_init(*routes):
    for path in routes:
        for parent in parents(path):
            initiate(parent)
        for module in path.rglob('*.py'):
            for parent in parents(module):
                initiate(parent)

def check_legacy(module, error):
    legacy = SOURCES / module.split('.')[0]
    if legacy.exists():
        legacy = SOURCES / module.replace('.', '/')
        if legacy.exists():
            sys.modules[module] = Mock()
            return True

        legacy = legacy.parent / f'{legacy.name}.py'
        if legacy.exists():
            imports = IMPORTS / f'{module.replace(".", "_")}.py'
            if not imports.exists():
                imports.write_text(legacy.read_text())

            sys.modules[module] = Mock()
            module_loader(imports)
            return True

        raise Exception(f'Legacy module {module} not found')




def check_requirements(module, error):
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


def module_loader(module):
    success = False
    counter = 0
    while not success:
        try:
            importlib.import_module('.'.join(module.parts))
            success = True
        except ImportError as error:
            counter += 1
            if not check_legacy(error.name):
                check_requirements(error.name)
        except TypeError as error:
            # if "'Mock'" not in str(error) and "metaclass conflict" not in str(error):
            #     raise TypeError from error
            success = True
        except AttributeError as error:
            # if 'Mock object' not in str(error):
            #     raise AttributeError from error
            success = True
        except KeyError as error:
            #
            success = True
        except Exception as error:
            raise Exception(f'Can not continue due error {error}') from error
    return counter


if __name__ == '__main__':
    base_init(SOURCES, IMPORTS, REQUIREMENTS, MODULES)
    print('legacy stats', len([file for file in SOURCES.rglob('*.py')]))

    counter = 0
    for module in MODULES.rglob('*.py'):
        module_loader(module)

    counter = len(list(IMPORTS.rglob('*.py')))

    print('find {} dependencies'.format(counter))
