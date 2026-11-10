"""Stage existing public paths, excluding repository-only source and evidence."""
import argparse
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {'scripts', 'tests', 'docs', 'package.json', 'package-lock.json', 'README.md'}

def public_entries(root):
    return [p for p in root.iterdir() if not p.name.startswith('.') and p.name not in EXCLUDE]

def stage(root, output):
    root, output = root.resolve(), output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Staging output must be outside the checkout')
    if output.exists():
        raise ValueError('Refuse to replace an existing staging directory')
    entries = public_entries(root)
    if not (root / 'index.html').is_file():
        raise ValueError('Missing public home page')
    for entry in entries:
        if entry.is_symlink() or (entry.is_dir() and any(p.is_symlink() for p in entry.rglob('*'))):
            raise ValueError('Public symlinks are not supported')
    output.mkdir(parents=True)
    for entry in entries:
        if entry.is_dir():
            shutil.copytree(entry, output / entry.name)
        else:
            shutil.copy2(entry, output / entry.name)
    (output / 'deployment-version.json').write_text(json.dumps({
        'source_commit': os.environ.get('GITHUB_SHA'),
        'run_id': os.environ.get('GITHUB_RUN_ID'),
        'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'),
    }, indent=2) + '\n')
    files = [p for p in output.rglob('*') if p.is_file()]
    print(json.dumps({'public_files': len(files), 'bytes': sum(p.stat().st_size for p in files)}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    stage(ROOT, parser.parse_args().output)
