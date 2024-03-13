from collections import Counter
from pathlib import Path

from remove_hints import hints_collector
from ast_extractor import extract_all_imports

from utils import parser, RESULTS


def extract_and_hint(paths=None):
    collected_deps = extract_all_imports(paths)
    paths = [Path(path) for path in collected_deps['imported'].keys()]
    collected_hints = hints_collector(paths)

    type_hints_counter = {key:val for key, val in collected_hints.items() if len(val)}
    refactor_collector = {}
    for filename, typings in type_hints_counter.items():
        imported = collected_deps['imported'].get(filename)
        if imported:
            result = {cls for cls, *__ in typings} & set(imported['classes'])
            if len(result):
                refactor_collector[filename] = result

    report = RESULTS / 'refactor_collector_report.txt'
    with report.open(mode='w', encoding='utf-8') as destination:
        for filename, classes in refactor_collector.items():
            destination.writelines([f'{filename} {classes}\n'])

    print('files to refactor', len(refactor_collector))

    return collected_deps, collected_hints, refactor_collector


if __name__ == '__main__':
    init_args = parser.parse_args()
    extract_and_hint(init_args.filenames)