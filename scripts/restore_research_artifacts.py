#!/usr/bin/env python3
"""Restore losslessly packaged research CSVs before running historical checks."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def contained(relative):
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        raise ValueError('Artifact path leaves repository')
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Verify compressed original bytes without restoring files')
    args = parser.parse_args()
    records = json.loads((ROOT / 'docs/publishing/compressed_artifacts.json').read_text())['artifacts']
    for record in records:
        archive = contained(record['archive'])
        destination = contained(record['path'])
        if digest(archive) != record['archive_sha256']:
            raise ValueError('Archive hash mismatch: ' + record['archive'])
        if not args.verify and destination.exists():
            if digest(destination) != record['sha256']:
                raise ValueError('Refusing to overwrite a different existing file: ' + record['path'])
            print('Already restored:', record['path'])
            continue
        temporary = destination.with_name(destination.name + '.restoring')
        output = None
        try:
            if not args.verify:
                destination.parent.mkdir(parents=True, exist_ok=True)
                output = temporary.open('xb')
            h = hashlib.sha256()
            length = 0
            with gzip.open(archive, 'rb') as incoming:
                for block in iter(lambda: incoming.read(1024 * 1024), b''):
                    h.update(block)
                    length += len(block)
                    if output is not None:
                        output.write(block)
            if h.hexdigest() != record['sha256'] or length != record['bytes']:
                raise ValueError('Original-byte hash/size mismatch: ' + record['path'])
            if output is not None:
                output.close()
                output = None
                os.replace(temporary, destination)
            print(('Verified:' if args.verify else 'Restored:'), record['path'])
        finally:
            if output is not None:
                output.close()
    print(f'{len(records)} artifacts verified' + ('' if args.verify else ' and restored'))

if __name__ == '__main__':
    main()
