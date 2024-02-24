from pathlib import Path
import time

from fabric import task
import io
from contextlib import redirect_stderr, redirect_stdout


@task
def strip_hints(context):
    start = time.time()
    print(start)
    errors = []
    SOURCES = Path('legacy_strip_hints/')
    STRIPPER = Path('strip_hints/bin/strip_hints.py')

    for index, file_for_strip_tags in enumerate(SOURCES.rglob('*.py')):
        if (index % 50) == 0:
            print(index)
        try:
            context.run(f'python {STRIPPER.absolute()} {file_for_strip_tags.absolute()} --inplace', hide=True)
        except Exception as error:
            errors.append(str(file_for_strip_tags))
    end = time.time()
    print('elapsed time', end - start)
    print('errors', len(errors))
    Path('errors_strip_hints.txt').write_text('\n'.join(errors), newline='\n')


@task
def remove_unused_imports(context):
    start = time.time()
    print(start)
    errors = []
    SOURCES = Path('legacy_strip_hints/')

    for index, file_for_strip_tags in enumerate(SOURCES.rglob('*.py')):

        if (index % 50) == 0:
            print(index)

        err_catcher = io.StringIO()
        with redirect_stderr(err_catcher):
            context.run(f'autoflake --remove-all-unused-imports --in-place -v {file_for_strip_tags.absolute()}')
        err_output = err_catcher.getvalue()
        if err_output:
            print('error', err_output, file_for_strip_tags)
            errors.append(str(file_for_strip_tags))

    end = time.time()
    print('elapsed time', end - start)
    print('errors', len(errors))
    Path('errors_unused_imports.txt').write_text('\n'.join(errors), newline='\n')

