from readable import ReadableAST
from pathlib import Path
from collections import Counter
# 'flesch_kincaid',
# 'flesch',
# 'gunning_fog',
# 'coleman_liau',
# 'dale_chall',
# 'ari',
# 'linsear_write',
# 'smog': all_sentences=True,
# 'spache',

if __name__ == '__main__':
    max_rate = 0
    method = 'flesch_kincaid'
    for project in ('winepad', 'django', 'fastapi', 'voice', 'healthcare', 'wpshop'):
        folder = Path(__file__).parent / f'legacy_{project}'
        idx = 0
        idx_summ = 0
        quantity = 0
        current_rate = 0
        counter = Counter()
        for idx, filename in enumerate(folder.glob('**/*.py'), start=1):
            current_rate = main(filename).readability(method)
            counter.update([int(current_rate)])
            for key in counter.keys():
                if key > 0:
                    idx_summ += key
                    quantity += counter[key]
                    max_rate = max(current_rate, key)

        avg_rate = idx_summ / max(quantity, 1)

        print('project', project, 'total files', idx, 'max rate', max_rate, 'avg rate', avg_rate)
