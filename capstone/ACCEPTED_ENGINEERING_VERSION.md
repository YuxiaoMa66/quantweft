# Capstone Engineering Example: Scope and Limits

The offline engineering example links a constructed input to signals, target positions, simulated fills, a ledger, risk checks, reconciliation, and a report. Its reader entrypoints are [engineering instructions](ENGINEERING_BASE.md), [offline runner](run_offline.py), [constructed configuration](configs/offline_constructed.json), [data dictionary](data_dictionary.md), and the [report template](research_report/report_template.md).

The example uses constructed data. It does not connect to a broker or produce French-market monthly returns. The French monthly-return design has no implemented ledger adapter, and the historical availability, ingestion, and revision times remain unknown. It therefore supplies no market result or strategy conclusion.
