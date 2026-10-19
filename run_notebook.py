#!/usr/bin/env python3
"""Execute a reader Notebook in a fresh kernel; preserve failure output under runs/."""
from pathlib import Path
from uuid import uuid4
import argparse, json, sys
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('notebook', help='Package-relative .ipynb path')
args=parser.parse_args()
source=(ROOT/args.notebook).resolve()
if not source.is_relative_to(ROOT) or source.suffix!='.ipynb' or not source.is_file():
    parser.error('Expected an existing Notebook inside this package')
out=ROOT/'runs'/('execution_'+source.stem+'_'+uuid4().hex)
out.mkdir(parents=True)
nb=nbformat.read(source,as_version=4)
status={'notebook':str(source.relative_to(ROOT)),'status':'RUNNING','interpreter':sys.executable}
try:
    NotebookClient(nb,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
    status['status']='PASS'
except Exception as exc:
    status.update(status='FAIL',error=str(exc))
    raise
finally:
    nbformat.write(nb,out/source.name)
    (out/'execution.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':status['status'],'evidence':str(out)},ensure_ascii=False))
