from pathlib import Path

from extract_and_hint import extract_and_hint

from utils import parser, RESULTS, SOURCES, base_init

import autoflake
from contextlib import redirect_stderr
import io
import os


def perform_extraction(paths=None):

    collected_deps, collected_hints, refactor_goals = extract_and_hint(paths)

    destination = RESULTS / 'extracted'
    breakpoint()
    for filename in collected_deps['imported'].keys():
        source = Path(filename)
        destination = RESULTS / 'extracted' / source.absolute().relative_to(SOURCES.absolute())
        base_init(destination)
        destination.write_text(source.read_text())

    for filename, hints in refactor_goals.items():
        source = Path(filename)
        with source.open(mode='r', encoding='utf-8') as sourcefile:
            destination = RESULTS / 'extracted' / source.absolute().relative_to(SOURCES.absolute())
            base_init(destination)
            lines = {}

            imported_classes = collected_deps['imported'][filename]['classes']
            for name, lineno, start_col, end_col in collected_hints[filename]:
                imported_module = imported_classes.get(name) or imported_classes.get(name.partition('.')[0])
                if name in hints and imported_module and imported_module.partition('.')[0] not in collected_deps['requirements']:
                    lines[lineno] = lines.get(lineno, []) + [(name, start_col, end_col)]

            with destination.open(mode='w', encoding='utf-8') as destination:
                for index, line in enumerate(sourcefile, 1):
                    if index in lines:
                        for name, start_col, end_col in sorted(lines[index], key=lambda val: val[2], reverse=True):
                            before, current, after = line[:start_col], line[start_col:end_col], line[end_col:]
                            current = current.strip().strip("'\"`")
                            if current != f'{name}'.strip():
                                raise ValueError(f'{name} does not match {current}')
                            line = "'".join([before, 'typing.Any', after]) # i put any in the place of the hint

                    destination.writelines([line])

    # '    with (RESULTS / 'autoflake_unused_imports.txt').open(mode='w', encoding='utf-8') as autoflake_results:
    #         with (RESULTS / 'autoflake_unused_imports_errors.txt').open(mode='w', encoding='utf-8') as autoflake_errors:'
    for file_for_strip_tags in (RESULTS / 'extracted').rglob('*.py'):
        if file_for_strip_tags.name != '__init__.py':
            os.system(f'autoflake --remove-all-unused-imports --in-place --verbose {file_for_strip_tags.absolute()}')

    print('files extracted, hints removed')


if __name__ == '__main__':
    init_args = parser.parse_args()
    perform_extraction(init_args.filenames)