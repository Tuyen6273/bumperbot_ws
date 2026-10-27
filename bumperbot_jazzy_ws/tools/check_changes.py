#!/usr/bin/env python3
"""Verify delivered files or check that the original workspace is untouched."""
import argparse
import hashlib
import json
import stat
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original', type=Path, help='Path to the original Humble workspace')
args = parser.parse_args()
workspace = Path(__file__).resolve().parents[1]
manifest = 'original_sha256.json' if args.original else 'delivered_sha256.json'
root = args.original.resolve() if args.original else workspace
expected = json.loads((workspace / 'migration' / manifest).read_text())
changed = []
for name, sha in expected.items():
    path = root / name
    if not path.is_file():
        changed.append(('MISSING', name))
    elif hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        changed.append(('MODIFIED', name))
exec_manifest = 'original_exec_bits.json' if args.original else 'delivered_exec_bits.json'
for name, bits in json.loads((workspace / 'migration' / exec_manifest).read_text()).items():
    path = root / name
    if path.is_file() and stat.S_IMODE(path.stat().st_mode) & 0o111 != bits:
        changed.append(('EXEC_PERMISSION', name))
for state, name in changed:
    print(state, name)
print(f'Checked {len(expected)} files; {len(changed)} differences.')
print('Checks tracked file contents only; extra files/build outputs are not compared.')
raise SystemExit(bool(changed))
