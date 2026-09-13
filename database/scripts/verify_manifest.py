"""Verify the immutable input data and SQL release without connecting to MySQL."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'manifest.json').read_text())
for relative,expected in manifest.items():
    path=ROOT/relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise SystemExit(f'Checksum mismatch: {relative}')
print(f'PASS: {len(manifest)} release files match their SHA-256 checksums.')
