import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from quant_course.risk import empirical_var_es

result = json.loads(Path(sys.argv[1]).read_text())
case = result["pinned_discrete_case"]
counts = np.rint(np.asarray(case["probabilities"]) * case["scenario_count"]).astype(int)
losses = np.repeat(case["loss_values"], counts)
var, es = empirical_var_es(losses, case["alpha"])
assert np.isclose(var, case["var"]) and np.isclose(es, case["es"])
assert losses[losses > var].mean() == case["strict_tail_conditional_mean"]
assert losses[losses >= var].mean() == case["inclusive_tail_conditional_mean"]
for bad_values, bad_alpha in (([np.nan], case["alpha"]), (losses, np.nan)):
    try:
        empirical_var_es(bad_values, bad_alpha)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("non-finite input must be rejected")
print(var, es)
