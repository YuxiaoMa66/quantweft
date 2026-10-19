"""Read-only cash check for the same CLI state database and run key."""
from pathlib import Path
import sqlite3,sys
state,key=Path(sys.argv[1]),sys.argv[2]
assert state.is_file(),"Complete the same constructed CLI first"
with sqlite3.connect(state.resolve().as_uri()+"?mode=ro",uri=True) as db:
    count=db.execute("SELECT COUNT(*),COUNT(DISTINCT fill_id) FROM fills WHERE run_key=?",(key,)).fetchone()
    spent=db.execute("SELECT SUM(signed_quantity*fill_price+commission) FROM fills WHERE run_key=?",(key,)).fetchone()[0]
assert count==(2,2)
assert spent is not None and abs(spent-2004.002)<=1e-6
assert abs((10000-spent)-7995.998)<=1e-6
print(count,spent,"USD; final cash",10000-spent)
