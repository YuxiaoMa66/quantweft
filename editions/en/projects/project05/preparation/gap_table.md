# Project 5 Gap Table

These are gaps in the A5 screening-preparation layer, not claims that the later c5/ALIGN constructed implementation is missing. Real-data, rights, and point-in-time gaps remain; a constructed implementation does not close them.

| Missing item | Impact | Treatment in this layer | Who must supply it |
|---|---|---|---|
| Security-level adjusted prices (including corporate actions) | Real pair screening and backtesting cannot be performed | Demonstrate with aggregated French industry portfolios; label them non-tradable | User supplies or authorizes a data source |
| Historical universe and delistings | Survivorship bias | No securities are used, so this is not addressed; no claim of unbiased results | Same |
| Borrow availability, fee, and recall | Cost and feasibility of the short leg | Not implemented; listed under not_included | Same |
| Two-leg cost convention | Net returns | Not implemented | Same |
| available_at (data-availability time) | Point-in-time validity | Not available for French data; declared non-point-in-time | Cannot be supplied |
| Entry/exit, risk controls, trading lag, flat-position state | Strategy layer | Not implemented (required by the contract) | Complete Project 5 phase |
| Multiple out-of-sample walk-forward windows | Robustness | Gives only “post-training-window diagnostics” for two windows; does not evaluate walk-forward performance | Complete Project 5 phase |
| Structural-break and cointegration-breakdown tests | Failure windows | Describes only frozen-spread half-life and ADF; no breakpoint test | Complete Project 5 phase |
| Diagnostics when the subsequent window contains missing values | Frozen-spread ADF and half-life require a complete monthly series | Validate screening and the subsequent window separately. The training segment must include train_end; the subsequent window must contain exactly every month from the month after train_end through test_end, once each. Missing months, missing endpoints, duplicates, an empty window, NaN, or infinity raise an error; no imputation or time compression is used. Data after test_end is not included in validation. | The complete Project 5 phase must decide the real-data missingness rule; the preparation layer rejects incomplete input |
