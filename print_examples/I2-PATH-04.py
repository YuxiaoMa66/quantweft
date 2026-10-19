import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from quant_course.risk import scenario_pnl

result = json.loads(Path(sys.argv[1]).read_text())
case = result["ledger_stress_and_limit"]
names = list(case["positions_at_signal_shares"])
pnl = scenario_pnl(
    [case["positions_at_signal_shares"][a] for a in names],
    [case["mark_prices_at_signal_currency_per_share"][a] for a in names],
    [case["overnight_gap_simple_returns"][a] for a in names],
)
loss = -float(pnl.sum())
risk = case["risk_limit"]
scale = risk["loss_cap_currency"] / loss
assert round(loss, 4) == case["conditional_stress_loss_currency"]
assert round(scale, 7) == risk["scale_factor"]
assert all(fill["quantity"] < 0 for fill in risk["actual_execution_fills"])
print(loss, scale, risk["target_weights_after_limit"], risk["actual_close_weights_after_execution"])
