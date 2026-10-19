# Project 1 Complete Solutions

> All six original answers are retained. Historical-report answers refer to the October 5, 2026 French snapshot, not to new Seed101 Notebook outputs.

## 1. Compounding and two return measures

Wealth rises from 100 to 110, then falls to 99. Cumulative two-month simple return is `99/100 − 1 = −1%`. The arithmetic mean is `(10% − 10%) / 2 = 0%`. Mean log return is

\[
\frac{\log(1.10)+\log(0.90)}{2}=\frac{\log(0.99)}{2}\approx-0.5025\%\text{/month}.
\]

The arithmetic mean averages the two monthly returns. Wealth multiplies their growth factors, `1.10 × 0.90 = 0.99`. Logs convert this time-series multiplication to addition; exponentiating the mean log return gives the monthly geometric return, approximately −0.5013%.

## 2. Read the report

HiTec’s 2010–2019 wealth index is approximately 4.6270, starting at 1, for cumulative return of approximately 362.70%. Under the convention of 120 months equal to 10 years, CAGR is 16.55%; multiplying sample volatility by `√12` gives 15.61%. These are descriptive statistics for one fixed historical window. Inputs are subsequently revised published industry portfolio returns without historical availability clocks, signals, trades or costs. They establish neither future performance nor a tradable strategy.

## 3. Same-month RF

Arithmetic excess return is `2.0% − 0.4% = 1.6%`. Subtracting annual 4% from every monthly return treats an annual unit as a monthly unit. This is neither a same-interval comparison nor an effective-rate conversion. Use the published monthly RF when analyzing monthly returns.

## 4. Peak drawdown

Wealth is 1.00, 1.50, 0.75, 1.20. Drawdowns from the running peak are 0%, 0%, −50%, −20%, so maximum drawdown loss is 50%. Full-path cumulative return is `1.20 / 1.00 − 1 = 20%`. Intermediate wealth relative to initial capital gives `0.75 / 1.00 − 1 = −25%`, whereas its drawdown from the peak of 1.50 is −50%. Cumulative return uses initial wealth as its denominator; drawdown uses a historical peak and depends on path order.

## 5. Compare segments

In 2010–2014, NoDur CAGR is 17.05%, exceeding HiTec’s 14.84% and Enrgy’s 7.88%. In 2015–2019, HiTec’s 18.30% exceeds NoDur’s 7.41%; Energy is −1.84%. Growth rankings therefore vary with the fixed interval. Energy’s annualized 2015–2019 Sharpe is approximately −0.033 because mean monthly excess return is slightly negative (−0.0578%) in that sample. This is not a guaranteed-loss law. Both intervals and the later segment are retrospective historical slices without real-time vintages, strategy signals, executions, costs or a reserved out-of-sample evaluation.

## 6. Read the figures

- Wealth index compounds monthly simple returns across time, showing how the specified path accumulates. Initial wealth 1 near December 2009 is a chosen normalization, not a market price.
- Rolling volatility uses the current month and previous 11 months to estimate a 12-month sample standard deviation and multiply it by \(\sqrt{12}\). It displays changing local dispersion. Until 12 observations exist, the window is incomplete and the first 11 months are blank.
- Drawdown shows wealth below its preceding peak. A value of −0.5 means 50% below that peak.
- Boxplots summarize full-window monthly simple returns. The center line is the median, boxes span quartiles and individually plotted points display more distant observations. The horizontal axis identifies fixed industry portfolios; the vertical axis uses decimal monthly returns.
