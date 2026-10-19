# Project 4 — Signal Preparation: Value, Momentum, and Quality

This is a preparation layer, not a complete Project 4. It covers point-in-time (PIT) fundamental selection, a field contract, fixed preprocessing/combination rules, and counterexamples. It contains no transaction-cost, borrowing/financing, capacity, or walk-forward evaluation and no results about real firms or real factor returns. No security-level PIT statements, prices, or historical universe are available here. Every number uses a constructed teaching universe with seed 20261210 and a known data-generating process. Complete real-market evidence remains unverified.

## Contents and boundaries

| Item | Status | File |
|---|---|---|
| Dictionary: fields, units, keys, times, missingness | Available | `data_dictionary.md` |
| Source feasibility: historically read SEC data-set documentation and price/universe gaps | Available | `source_feasibility.md` |
| PIT events: period-end, acceptance, ingestion, signal/trade times, labels, restatement/delisting | Available | `pit_event_graph.md` |
| Value/Momentum/Quality contract | Available | `configs/signal_contract.json`, `field_contract.md` |
| Fixed winsorize→neutralize→z-score, combination, quintiles, industry projection | Frozen configuration/hash, not external preregistration | `configs/frozen_rules.json`, `rules.md` |
| Reader Notebook, six counterexamples, historical engineering entry points | Default uses Notebook only; historical CLI/tests are outside offline execution scope | `notebooks/p04_signal_layer.ipynb`; local repository for engineering sources |
| Constructed/real labels and gaps | Available | This file, `gap_table.md` |
| Costs, borrowing/financing, capacity, walk-forward, ablation/robustness, report | Absent from this signal layer | — |
| Real security-level PIT statements, prices/total returns, membership/delistings | Missing | `gap_table.md` |

## Label every data/result type

| Data or result | Type |
|---|---|
| 240 firms:200 nonfinancial and 40 banks;96 months January 2014–December 2021;2,257 filing versions including 97 restatements;29 delistings | Constructed teaching universe with no built-in value/momentum/quality effect |
| Availability 60–110 days after year-end; restatements 130–260 days later | Constructed rule; real availability requires SEC acceptance, subject to source checks |
| Rolling Rank-IC diagnostics | Historical constructed zero-effect world, $t$ near±1; nonsignificance alone does not establish absence of leakage, so causal perturbations are checked separately |
| French five factors/ten industries | Real aggregate data, not used by this layer and unsuitable for security-level signals |

## Default offline reading and outputs

Runtime and user-input contracts follow the accepted reader package's [shared instructions](../../../NOTEBOOK_GUIDE.md); see the [guide](../READER_GUIDE.md) for both language entry points. The default runs constructed Notebook cells only, not historical CLI/pytest. The first cell creates `runs/p04_signal_layer_<uuid>/`; its image goes to `figures/a5/p04_signal_layer.png` inside that directory. The runner separately saves execution copy/status without writing frozen sources. Language projections preserve I 3 code/output/metadata identity and change Markdown only.

“Historical independent evidence, not bundled” identifies a historical source; it is neither an executable path nor a current output directory. The following A5/A6 results are retained historical numbers and are not revalidated by the default Notebook. The original independent recomputation selected PIT values and seven fields cell by cell from version tables and repeated the preprocessing chain in numpy without course signal helpers. It is not rerun in this edition.

## A5 historical constructed results: retain identity and values

**Timing perturbation.** Changing all post-June 2018 contents—returns, cap, and later-available fundamentals multiplied by 3—left the seven fields/composite bitwise unchanged through the cutoff,54 months, maximum difference 0. Later composite values changed, maximum 1.87. This supports the selected no-lookahead check and confirms a real perturbation; it is not a proof for arbitrary inputs.

**Use period-end as availability: lookahead.** About 18–20% of company-months use filings not yet submitted: B/M 20.3%, earnings yield 20.5%, ROE 20.4%, GP/A18.1%. For February/March signal months whose filings enter in March/April, naive-minus-PIT leakage correlates with next-month returns: B/M 0.079 ($t=3.8$,14 months), GP/A0.078 ($t=4.1$). Earnings yield/ROE are near 0 because constructed news enters assets rather than income; other months are near−0.01 from restatements. This is a constructed leakage channel, not a real-market effect estimate.

**One-version restatement rule.** P102 FY2013 original available 2014-04-17: income 6.26/equity 230.13; amendment available 2014-05-20: income 5.36/equity 213.54. April uses the original, May onward the amendment. Mixed numerator/denominator ROE 2.33% differs from same-version 2.72% before and 2.51% after.

**Survivor-only universe.** In June 2019, keeping final survivors removes 13 names:224 versus 211. Next-month equal-weight returns are 1.13% versus 1.19%; all-month mean 0.818% versus 0.833%. There are 29 later delistings with assumed−25% delisting-month return.

**Nonpositive denominators and financial firms.** Of 20,579 listed cells,240 have nonpositive equity: naive B/M is negative, minimum−0.357; policy sets NaN, smallest positive 0.0006. Naive EV/EBITDA has 90 negative values, excluded under the rule. Bank EV/EBITDA and GP/A are missing. Mean field coverage among listed names: B/M 96.3%, earnings yield 97.4%, EV/EBITDA 80.4%, momentum 86.1%, GP/A80.8%, negative accrual 97.4%, ROE 94.7%.

**Full-sample standardization.** Full-sample per-name time-series z-scores of the composite disagree in sign with past-only expanding values in 11.2% of 17,258 cells.

**A5 historical portfolios/exposures, before protocol correction and without costs.** Quintile long–short gross 2.0, net below$10^{-16}$, mean maximum absolute industry net 0.062, mean absolute log-cap exposure 0.133. Old industry projection: gross 2.11, industry net$3\times10^{-17}$, size exposure 0.094. These are historical full-column projection values, not a new current-C13 run. This signal layer reports no return/Sharpe strategy evaluation.

**Zero-effect IC diagnostics.** Value 0.0024 ($t=0.35$), momentum 0.0056 (0.85), quality 0.0074 (1.02), composite 0.0071 (1.03). Momentum has 84 evaluation months because 12–1 needs a 12-month formation history; the others have 93. Nonsignificance is a historical diagnostic baseline, not proof of zero effects or no leakage. Real IC needs security-level PIT data.

**Attempt counts.** Seven raw fields, three styles, one composite, two portfolio methods, one fixed IC-diagnostic set, six rule counterexamples rather than alternative strategies. The historical record states that winsorization 1%/99%, ddof 1, minimum counts, and weights were written in `frozen_rules.json` before labels were viewed; local hashes alone do not independently prove that precedence.

## Time fields

`event_time` is fiscal period-end or return month. `available_at` is public filing availability, constructed here; real applications require verified SEC acceptance. `ingested_at` is one day later in this universe. `signal_time` is the last instant of month-end UTC. `trade_time` is the first subsequent tradable price; next-month labels approximate this at monthly frequency, not daily precision. Return/label intervals are the next calendar month. A version is usable in month$t$ iff both availability and ingestion strictly precede the first instant of the next month UTC; see `pit_event_graph.md`.

## Current support protocol and historical findings

Old A5 projected on all 240 columns and A6 then zeroed unlisted names. Retained evidence includes 1,842 off-support name-months and maximum post-filter industry net 0.0280748663. Current C13 corrects that mismatch: [protocol](../../../../../projects/project04/SIGNAL_PORTFOLIO_PROTOCOL_ALIGNMENT.md), [support entry](../../../../../projects/project04/ACCEPTED_PORTFOLIO_SUPPORT_20261014.md). Preserve old numbers/negative findings without calling the issue still unfixed or relabeling them as new results.

The current method requires at least 60 signal-date listed names; an ineligible date has missing signals and cash targets. Optional industry projection builds rows only on listed support and may use listed names without alpha as hedges. Off-support weights are zero. After homogeneous industry/net-zero projection, restore gross 2 with one scalar; no direction or degeneracy means explicit cash. This is not a pure extreme-quintile portfolio and does not guarantee neutrality after execution. The fixed current constructed run has mean neutral-target gross 2 and off-support weight 0. Cancellations, partial fills, and price drift are a separate clock, reported in the protocol note.

This set completes signal teaching only. Full cost/execution/backtest explanations, dictionary, historical report, and six complete solutions continue with Chapters 29–31; Chapters 35–36 revisit execution consumers. Real PIT data, financing/borrowing, and capacity remain missing. The complete real-market project remains planned.
