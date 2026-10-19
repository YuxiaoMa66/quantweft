# Research Question, Sources, and Prior Exposure

\color{qink}


The [README](README.md) states the current technical acceptance and stopping point. This document explains why M0 is compared with EW10 and what inputs can answer the question. Full parameters are in the [protocol](PROTOCOL.md) and the original-byte [French protocol config in the read-only I3 source](../../../capstone/configs/french_protocol_v2.json).

## Primary question and hypotheses

\color{qink}


In the accepted primary reporting window, 2015-09..2026-08 (future execution still requires authorization), does a fully invested long-only strategy that ranks industries by total return over the preceding 11 months ($t-12,\ldots,t-2$ for holding month $t$), holds the top three equally, and rebalances monthly produce a higher average net monthly return than the monthly equal-weight benchmark across ten industries, under the same 10 bps per unit of traded notional cost?

The economic-mechanism hypothesis is that common industry-level shocks and slow information diffusion may lead to medium-term return continuation. Reversal, industry risk premia, or concentration could produce the same observation. This study tests only the return difference; it does not identify a causal effect of “slow diffusion.” Skipping the most recent month is a fixed signal definition, not a demonstrated reversal effect or evidence about data availability. Do not use unread papers to supply conclusions about the established literature.

The experimental unit is one calendar holding month's paired portfolio net-return difference, $d_t=r_{M,\mathrm{net},t}-r_{EW,\mathrm{net},t}$. The ten industries form that month's signal cross-section; they are not ten independent monthly replications. The primary endpoint is $\mu_d=E[d_t]$ (decimal per month). The directional alternative is $H_1:\mu_d>0$, with null $H_0:\mu_d\le 0$; assess it using the prespecified one-sided 95% lower bound and paired HAC inference over the monthly sequence. Economic significance is considered separately: whether the average net advantage reaches the illustrative prespecified threshold of 10 bps/month, alongside wealth, drawdown, and concentration. The threshold is a design judgment, not calibrated to actual capital costs.

The simplest baseline assigns 10% to each of the ten industries each month, with the same execution, cost, entry, and exit rules as the strategy. Net return must first come from a self-financing ledger. Subtract RF once only for Sharpe or attribution; the primary paired difference cancels the common same-month RF. There is no model training, factor screening, or maximum-Sharpe optimization.

Negative and zero outcomes also complete the research. If the interval crosses zero, evidence is insufficient under the sample and dependence assumptions. If the net mean is $\le 0$, report that this specification did not achieve a net advantage. If a gross advantage is consumed by costs, report the cost sensitivity. A non-significant result does not prove the strategy is always ineffective. If a data or licensing gate fails, the conclusion is feasibility-blocked, not a zero result from a market test.

## Input: total-return portfolio categories, not OHLCV

\color{qink}


The ten industries are supplier portfolio categories, not permanent security IDs; monthly returns follow the supplier's total-return convention. The observation is one paired portfolio return difference for a month, not ten independent industry experiments. The selected route can compare portfolio-level differences under fixed revised history and hypothetical costs. The institution-level, security-by-security PIT route was not selected; the P5 requirement for 16 assets and the P6 data-span requirement do not carry over.

Fixed input identity: `French_20261005_revised_history_A10A_v1`; snapshot date 2026-10-05; vintage 202608; coverage 1926-07..2026-08, 1,202 months. Industry download time in UTC: `2026-10-05T19:18:24.585420+00:00`; FF3 download time: `2026-10-05T21:11:10.296518+00:00`. Convert the original percentages to decimals once only. This edition reuses metadata from the accepted materials; it did not read new CSV/ZIP bytes or recompute data statistics. Names, hashes, and units are in the [read-only I3 source-identity map](../../../capstone/accepted_source_map.json). This package does not distribute the research-market CSV/ZIP files.

Historical source review was limited to the official ten-industry construction, coverage, and copyright sections; the factor RF/definition sections; the data homepage sections on revisions/format changes; and the CRSP changes body. The linked CRSP PDF was not read. Do not use that unread PDF or unchecked papers to prove the mechanism. This edition did not browse the web and makes no claim of new source review or of an absence of licensing terms across the whole site. Prior ICBC plans and older rights tables are historical records only; the current actual subject and use are unknown and are not presumed to be individual or bank-internal. Public download and copyright attribution do not replace rights evidence for the actual activity.

## Exposure, degrees of freedom, and future access

\color{qink}


| Prior exposure | Known range and basis | Influence on the choice | Boundary |
|---|---|---|---|
| P1 | README and manifest: NoDur / HiTec / Enrgy for 2010–2019, with descriptive results for 2020–2024 | Carry forward unit and snapshot review; industry-wealth measures have already been shown | The historical design batch did not recompute its measures |
| P2 | README/config: nine realized CAPM / FF3 / FF5 groups for 2010–2019; estimate on 2010–2014 and same-month attribution on 2015–2019 | Choose FF3 rather than mixing FF3 and FF5; carry forward monthly RF/HAC conventions | Attribution is not prediction, and alpha does not decide whether momentum wins |
| P3 | README/config: full ten-industry history 1990-01..2026-08; 60-month primary specification and multiple window/cost sensitivities; public report did not credibly find three estimated portfolios better than equal weight | Use a simple equal-weight baseline to reduce model search; this choice has a hindsight component | Net results and benchmark exposure already exist over the same history; it cannot be called an unused holdout |
| P4 | Cost-preparation README/acceptance entry: constructed signals, share ledger, and cost/execution experiments | Adopt exact cost-ledger boundaries and avoid residuals from industry-neutral projection | Constructed costs do not calibrate real markets |
| P5 | Manifest/acceptance identity: paired constructed study; real panel blocked; 16-asset historical requirement belongs to P5 | Do not inherit its assets/dates or choose a model based on paired performance | Not every constructed-performance row was reread; user/old-session exposure history is unknown |
| P6 | Manifest/acceptance identity: baseline/tree-model constructed results and later presentation revisions; real study blocked and overall status not verified | Do not add an ML contest; reuse time-contract gates | The missing row-level predictions for Chapter 39 and the failed-artifact gaps remain open; do not claim the evidence is complete |

\color{qink}


Access by other sessions or people to the target momentum question is unknown; historical test status is `exposed_or_unknown` and `full_preregistration=false`. Locked reporting constrains future target runs and changes; it does not retroactively make the history a blind holdout.

Before any first authorized target run, preserve the run manifest, code/config/data hashes, all 13 prespecified paths, seed, accessors, and UTC times. Report the primary result and every prespecified sensitivity together, including positive, zero, and negative outcomes. Do not change parameters after viewing locked reporting. Preserve failed inputs and outputs for technical retries and show that the repair did not depend on returns. New economic hypotheses or performance-driven revisions require a new version and must be labeled as post-hoc exploration. A genuinely unused future sample must be supported by access records and frozen separately; do not invent future dates. No training, screening, fitted transformation, or maximum-Sharpe optimization is included.

The [18-item report guide](research_report/REPORT_GUIDE.md) turns the question into input → action → output → interpretation. The [time contract](TIME_CONTRACT.md) explains unknown historical clocks and label maturity.
