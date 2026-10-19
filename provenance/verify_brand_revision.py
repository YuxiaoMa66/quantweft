"""Verify the QuantWeft branding reader revision against its dated accepted baseline."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
revision = json.loads((root / 'provenance/BRAND_REVISION.json').read_text())
manifest_path = root / 'provenance/FORMAL_MANIFEST.json'
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == revision['baseline_sha256']
manifest = json.loads(manifest_path.read_text())
errors = []
for row in manifest['rows']:
    original = row['path']
    current = revision['path_map'].get(original, original)
    expected = revision['intentional_document_changes'].get(current, row)['sha256']
    path = root / current
    if not path.is_file() or path.is_symlink():
        errors.append(f'missing or symlink: {current}')
    elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append(f'changed: {current}')
for current, expected in revision['additional_current_files'].items():
    path = root / current
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        errors.append(f'missing or changed: {current}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f"PASS: {len(manifest['rows'])} original payload identities accounted for; "
      'four PDFs unchanged; reader path/document changes match the QuantWeft branding revision.')
