"""Small path-adaptation check: fixed offline config, resume/idempotence and reconciliation."""
from pathlib import Path
from uuid import uuid4
import json, sys, sqlite3
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from quant_course.production_pipeline import run_pipeline
cfg=json.loads((ROOT/'capstone/configs/offline_constructed.json').read_text())
run=ROOT/'runs'/('capstone_recovery_'+uuid4().hex);run.mkdir(parents=True)
args=dict(config=cfg,run_key='constructed-portable',state_db=run/'state.sqlite',output_dir=run/'artifacts')
try:
    run_pipeline(**args,fault='after_first_fill')
except RuntimeError as exc:
    print('Expected fault retained:',str(exc))
else:
    raise AssertionError('Expected fault injection')
result=run_pipeline(**args)
assert result['reconciliation']['status']=='PASS'
assert abs(result['terminal_nav']-9995.998)<1e-6
conn=sqlite3.connect(run/'state.sqlite')
counts_before={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['fills','runs']}
replay=run_pipeline(**args)
counts_after={name:conn.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['fills','runs']}
assert counts_before==counts_after and result==replay
conn.close()
(run/'check.json').write_text(json.dumps({'status':'PASS','scope':'CONSTRUCTED fixed config recovery/idempotence/path adaptation only','counts_before':counts_before,'counts_after':counts_after,'summary':result},indent=2))
print('PASS',run)
