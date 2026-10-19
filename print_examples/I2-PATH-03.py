import sys
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location("ch33", ROOT / "code/ch33_risk_management.py")
ch33 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch33)
from quant_course.portfolio_construction import exposure_report

result = json.loads(Path(sys.argv[1]).read_text())
inputs = ch33.INPUTS["ledger_stress"]
weights = np.asarray(inputs["initial_target_weights"])
report = exposure_report(weights, inputs["betas"], inputs["sectors"])
saved = result["exposures"]
assert report.net == saved["net_exposure"]
assert report.gross == saved["gross_exposure"]
assert report.beta == saved["market_beta"]
neutral = saved["neutrality_counterexample"]
assert neutral["net_leverage_on_nav"] == 0.0
assert neutral["gross_leverage_on_nav"] > 0.0 and neutral["beta"] != 0.0
print(saved["factor_exposures"], saved["concentration_hhi_within_gross_risk_assets"])
