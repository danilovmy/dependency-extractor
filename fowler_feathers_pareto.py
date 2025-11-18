import re
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter
import math


basepath = Path(__file__).parent
history = (basepath / 'django_log.txt').read_text()
#history = (basepath / 'davinchi_log.txt').read_text()
# Regular expression to extract file names from commit messages
#file_pattern = r'davinchi\/[a-zA-Z0-9_/.]+\.[a-zA-Z0-9]+'
file_pattern = r'django\/[a-zA-Z0-9_/.]+\.[a-zA-Z0-9]+'

files = re.findall(file_pattern, history)

# Count the number of commits for each file
file_counts = {}
for file in files:
    if file.endswith('.py'):
    # if not file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'), ):
        if file in file_counts:
            file_counts[file] += 1
        else:
            file_counts[file] = 1

counter_of_commits = Counter(file_counts.values())

file_counts = {k: v for k, v in file_counts.items() if v > 1}
# Sort the file counts in ascending order
sorted_file_counts = sorted(file_counts.items(), key=lambda x: x[1],)

# Separate the file names and counts into different lists

file_names = [idx for idx, x in enumerate(sorted_file_counts, start=1)]
counts = [x[1] for x in sorted_file_counts]


# call the plot_counter_of_commits function

# Plot the results in a 2D bar chart
plt.figure(1)
plt.bar(file_names, counts)
plt.xlabel('File Name')
plt.ylabel('Number of Commits')
plt.title('Commit History')
plt.xticks(rotation=90)  # Rotate the x-axis labels for better readability
plt.tight_layout()

most_common_commits = counter_of_commits.most_common()
most_common_commits = sorted(most_common_commits, key=lambda x: x[0])
files_with_same_quantity_of_commits = [x[1]/x[0] for x in most_common_commits]
commits_per_file = [x[0] for x in most_common_commits]
    # create the plot
plt.figure(2)
plt.bar(commits_per_file, files_with_same_quantity_of_commits)
plt.ylabel('files per quantity of commits')
plt.xlabel('commits per file (log scale)')
plt.title('Commit History')
plt.xscale('log')


plt.show()