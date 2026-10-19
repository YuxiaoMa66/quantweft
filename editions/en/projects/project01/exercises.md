# Project 1 Exercises

> Exercises 2 and 5 read the original [historical report](research_report/report.md). Their answers use the October 5, 2026 French snapshot, separate from the current Seed101 constructed output. The CLI at the end belongs to the historical course route; use the [reader guide](READER_GUIDE.md) for the offline Notebook.

Attempt these questions before consulting the [solutions](solutions.md). Return inputs are decimals; ignore external cash flows unless a question states otherwise.

1. **Compounding and two return measures.** Initial wealth is 100, followed by monthly simple returns of +10% and −10%. Calculate wealth at each month end, cumulative two-month simple return, arithmetic mean monthly return and mean monthly log return. Why do they differ?
2. **Read the report.** HiTec’s mean monthly simple return exceeds NoDur’s in 2010–2019. What wealth index, compound annual growth rate (CAGR) and volatility does the report give for HiTec? Do these values establish that “HiTec is a better future investment”? Explain.
3. **Same-month RF.** An industry returns 2.0% in a month whose RF is 0.4%. Calculate the arithmetic excess return. What unit or frequency error results from subtracting the year’s annual RF of 4% from every monthly return?
4. **Peak drawdown.** Wealth follows `[1.00, 1.50, 0.75, 1.20]`. Calculate drawdown from the running peak at every point and its maximum loss. Calculate the full path’s final cumulative simple return and explain why it differs from maximum drawdown. How does the intermediate wealth of 0.75, a −25% loss from the initial value, differ from maximum drawdown?
5. **Compare segments.** Use the results table to compare the three industries in 2010–2014 and 2015–2019. Which industry has the highest CAGR in each segment? How should the negative 2015–2019 Energy Sharpe ratio be interpreted? Does this test a future tradable strategy?
6. **Read the figures.** What questions do wealth index, rolling volatility, drawdown and boxplots answer? What does the initial point on the wealth figure’s time axis represent, and why are the first 11 months of rolling volatility blank?

Historical course-work route for regenerating the numerical tables:

```bash
.venv/bin/python projects/project01/run_project01.py
```
