import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from quant_course.risk import kupiec_pof

result = json.loads(Path(sys.argv[1]).read_text())
backtest = result["risk_model_backtest"]
test = backtest["test_window"]
calculated = kupiec_pof(test["realized_exceedances"], test["observations"], backtest["alpha"])
for count in backtest["boundary_count_checks"].values():
    if isinstance(count, dict):
        edge = kupiec_pof(count["exceedances"], count["n_obs"], backtest["alpha"])
        assert edge["lr_uc"] == count["lr_uc"]
        assert edge["p_value"] == count["p_value"]
assert abs(calculated["lr_uc"] - test["lr_uc"]) < 1e-8
assert calculated["p_value"] == test["p_value"]
print(calculated)
