# Project 4 Gap Table

| Missing input | Consequence | Signal-layer treatment | Responsibility |
|---|---|---|---|
| Company-level PIT fundamentals, restatements, `accepted`, and prior-year comparatives | No real value/quality signals | Constructed universe; see `source_feasibility.md` for the historical SEC-document reading scope. Tag mapping, time zones, and annual-value filtering remain unchecked | User-supplied data or separately authorized download, followed by verification |
| Security prices, total returns, delisting returns, corporate actions | No real momentum or labels | Constructed returns; −25% delisting-month return is an assumption | User-supplied or authorized source |
| Historical universe and constituent changes | Survivorship bias | Constructed as-of membership; no claim of a real universe | Same |
| Historical market cap and shares outstanding | Value ratios and size neutralization | Constructed month-end cap | Same |
| Historical industry classifications | PIT neutralization | Constructed static labels; SEC `sic` is filing-specific | Same |
| Daily prices and trading calendar | Next-tradable-time execution of closing signals | Monthly approximation, differing by up to one trading session; see rule 6 in `pit_event_graph.md` | Same |
| Beta and market data | Beta/exposure checks | Not implemented here; industry/size exposures only | Complete-project stage |
| Costs, borrowing/financing, capacity | Net returns | Absent from this signal layer; separate constructed cost/execution teaching does not establish real borrowing or capacity | Complete-project stage |
| Walk-forward, factor ablation, robustness, report | Complete project | Absent here; historical constructed ledger/cost reports exist, with replay distinct from new computation | Complete-project stage |
| Data rights and licenses | Permitted use/redistribution | No restricted data downloaded | User confirmation |
| Minority interest, preferred stock, nonoperating assets in EV | Real-company EV/EBITDA would not reconcile with Chapter 24; discrepancy depends on missing items | `versions` lacks these fields; zero is an explicit constructed-universe assumption only | Add and reconcile at the real-data stage |

This is a table of real signal-input gaps. It does not deny the existing constructed ledger and cost teaching. Listed-support projection is corrected under the current C13 protocol; real security-level data, trading eligibility, financing, and borrowing gaps remain.
