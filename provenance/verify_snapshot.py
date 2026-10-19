"""Verify the dated accepted baseline without changing files or running research."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'provenance/FORMAL_MANIFEST.json').read_text())
errors=[]
for row in manifest['rows']:
 p=root/row['path']
 if not p.is_file() or p.is_symlink(): errors.append((row['path'],'missing or symlink'));continue
 with p.open('rb') as f: digest=hashlib.file_digest(f,'sha256').hexdigest()
 if p.stat().st_size!=row['bytes'] or digest!=row['sha256']:errors.append((row['path'],'changed'))
if errors:
 for path,reason in errors: print(reason+': '+path)
 raise SystemExit(1)
print('PASS: all '+str(len(manifest['rows']))+' dated source files match accepted SHA-256 values.')
