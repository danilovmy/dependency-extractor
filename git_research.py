#!/usr/bin/env python3
"""
max_changes.py  –  Print the commit with the largest #files/#funcs/#classes
                   in a given date range.
Usage:
    python max_changes.py --repo /path/to/repo \
                          --since 2024-01-01 \
                          --until 2024-06-30
"""
import ast
import argparse
from datetime import datetime, timezone
from pathlib import Path

from pydriller import Repository


def count_defs(source: str, node_type):
    """Return how many ast nodes of *node_type* exist in *source*."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0       # skip non‑python or broken files
    return sum(isinstance(n, node_type) for n in ast.walk(tree))


def analyse_commit(commit):
    """Return (#files, #funcs, #classes) touched in *commit*."""

    functions, classes = 0, 0
    for mod in commit.modified_files:
        # we only parse files that still exist after the commit
        if mod.new_path and mod.source_code:
            functions += count_defs(mod.source_code, ast.FunctionDef)
            classes += count_defs(mod.source_code, ast.ClassDef)
    return commit.files, functions, classes


def main(repo_path=None, since=None, until=None):
    since_d = datetime.fromisoformat(since or '1970-01-01').replace(tzinfo=timezone.utc)
    until_d = datetime.fromisoformat(until or '2100-01-01').replace(tzinfo=timezone.utc)

    max_record = {
        "files": (0, None),
        "funcs": (0, None),
        "classes": (0, None),
    }

    for commit in Repository(
        repo_path or '/',
        since=since_d,
        to=until_d,
    ).traverse_commits():

        files, funcs, classes = analyse_commit(commit)
        print (f"{commit.hash}: {commit.committer_date} {commit.author.name}")
        # update maxima
        if files > max_record["files"][0]:
            max_record["files"] = (files, commit)
        if funcs > max_record["funcs"][0]:
            max_record["funcs"] = (funcs, commit)
        if classes > max_record["classes"][0]:
            max_record["classes"] = (classes, commit)

    # --- report ---
    for what, (qty, commit) in max_record.items():
        if commit is None:
            print(f"No commits found that changed any {what}.")
            continue
        print(f"\nMost‑changed {what[:-1]}s: {qty}")
        print(f"  sha:   {commit.hash}")
        print(f"  date:  {commit.committer_date}")
        print(f"  msg:   {commit.msg.splitlines()[0]}")
        print(f"  author:{commit.author.name} <{commit.author.email}>")
        print("  files:", ", ".join(Path(m.new_path or m.old_path).name
                                       for m in commit.modified_files[:10]),
              "..." if len(commit.modified_files) > 10 else "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=False, help="Path to the git repo")
    parser.add_argument("--since", required=False, help="YYYY‑MM‑DD (inclusive)")
    parser.add_argument("--until", required=False, help="YYYY‑MM‑DD (inclusive)")
    args = parser.parse_args()

    main(args.repo, args.since, args.until)
