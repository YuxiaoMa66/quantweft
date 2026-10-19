# Chapter 12 — Financial Statements for Quantitative Research

> The central task is to connect the income statement, balance sheet, and cash flow statement into company features with explicit units, periods, versions, and reproducible information-availability times.
> Prerequisites: Chapter 3 on data engineering and Chapter 10 on market instruments; Chapter 11 on returns and compounding provides background. After this chapter, you can explain the main links among the three statements; construct and interpret revenue, profit margins, cash flow from operations (CFO), capital expenditure (CapEx), free cash flow (FCF), working capital, and debt features; and prevent later restatements from leaking into earlier signals.

## 1. Learning Objectives

After reading this chapter, you should be able to do four kinds of work.

1. Trace an item in one statement to its effects on the other two. Given credit sales, depreciation, capital expenditure, or borrowing, explain how profit, balance-sheet accounts, and cash change.
2. Align the numerators, denominators, currencies, units, and periods of common financial features. Define explicit proxies for earnings before interest and taxes (EBIT), earnings before interest, taxes, depreciation and amortization (EBITDA), CFO, CapEx, FCF, selected operating working capital (Selected OWC), net debt, and FCF yield.
3. Preserve the reporting period, first public version, filing version, revision version, receipt time, and local ingestion time for every value. Determine which version was both public and in the research database at a given signal_time.
4. Check figures and definitions against actual statements. Recalculate the original Apple FY2024/FY2023 statement lines, distinguish Spire's original FY2023 10-K from its later 10-K/A, and explain what these limited cases do and do not establish.

The standard is reproducibility: a reviewer can use source links, accession numbers, statement line names, periods, and formulas to recalculate the results. Constructed data remain distinct from company disclosures, and late versions cannot overwrite values visible earlier.

## 2. Why Quants Need This

Factor research often compresses financial statements into a number, such as operating margin, CFO/assets, net debt/EBITDA, or FCF yield. Comparing numbers looks easy, but producing them requires choices: consolidated profit or profit attributable to the parent, ending or average assets, a negative CapEx cash-flow line or positive expenditure, the time a revision became public, and the time a vendor entered it into a database.

These choices can change rankings. One company may report revenue growth yet collect cash slowly because receivables grow faster; another may report lower profit but higher cash flow after collecting receivables. Higher CapEx depresses near-term FCF while potentially building future capacity. Accounting features are therefore measurements with definitions and versions, rather than truths obtained simply by reading a statement.

Financial statements describe a company and reporting period; security prices belong to tradable securities, share classes, and trading times. Mapping company data to common stock also requires checks of permanent security identifiers, listing classes, currencies, share capital, tradability, and time. Chapter 13 connects enterprise value to equity value. This chapter first establishes trustworthy statement inputs, without claiming that a factor earns excess returns.

## 3. Intuition

::: {.body-example title="Worked Example: Transactions, Three Statements, and Cash from 50 to 63"}

Consider a fictional company over one quarter. It delivers goods and services worth 100, collecting 80 in cash and selling 20 on credit. Cost of goods sold (COGS) is 40, cash operating expenses are 25, depreciation and amortization (D&A) are 10, interest is 5, and income tax is 4. The company buys equipment for 8 and borrows another 15.

All amounts use the constructed unit $u$, cover the same quarter, and describe one consolidated company with no noncontrolling interest (NCI). Opening accounts receivable (AR) and accounts payable (AP) are zero. There are no dividends, share issues, exchange-rate effects, or other adjustments beyond the listed transactions. Interest and income tax payments are classified in CFO in this example. Inventory purchases are 50: 40 paid in cash and 10 owed to suppliers. COGS of 40 leaves inventory up by 10 at quarter-end.

Purchases of property, plant and equipment (PP&E) belong to cash flow from investing activities (CFI); new borrowing belongs to cash flow from financing activities (CFF).

| Quarterly transaction | Income-statement effect | Balance-sheet account changes | Cash-flow classification and calculation |
|---|---|---|---|
| Deliver sales of 100: collect 80, sell 20 on credit | Revenue +100 | Cash +80, AR +20 | Direct method: cash from customers +80; indirect method: revenue already enters starting profit, so deduct the AR increase of 20 |
| Buy inventory of 50: pay 40, owe 10; recognize COGS of 40 | COGS −40 | Cash −40, net inventory +10, AP +10 | Direct method: supplier payments −40; indirect method: deduct inventory increase 10, add AP increase 10 |
| Pay cash operating expenses of 25 | Operating expenses −25 | Cash −25 | CFO −25 |
| Recognize depreciation of 10 | Depreciation expense −10 | Net PP&E −10 | Noncash expense: add back +10 in indirect CFO |
| Pay interest of 5 and income tax of 4 | Interest expense −5, tax expense −4 | Cash −9 | Both classified in CFO here: −5−4 |
| Buy equipment for cash of 8 | No immediate expense on purchase | Gross PP&E +8, cash −8 | CFI −8; positive CapEx expenditure = 8 |
| Borrow another 15 | No revenue or profit effect | Debt +15, cash +15 | CFF +15 |

The income statement gives gross profit $100-40=60$, operating income $60-25-10=25$, and net income $25-5-4=16$. This chapter's EBITDA proxy is $25+10=35$. Under these simplified assumptions, CFO is $35-5-4-20=6$, where 20 is the net increase in Selected OWC. The EBITDA proxy deducts neither interest, tax, nor working-capital changes; CFO reflects their operating cash effects, so the two are unequal. Check the same CFO by the indirect method: start with net income 16, add depreciation 10, deduct AR growth 20 and inventory growth 10, and add AP growth 10, totaling 6.

Of the six Selected OWC components, only AR, inventory, and AP change here: +20, +10, and +10, respectively, producing a net increase of 20. Vendor non-trade receivables, other operating current assets, and deferred revenue have zero changes. CFO already includes the cash effects of all six items. FCF deducts only the specified CapEx; do not deduct the same 20 from CFO again.

| Ending stock | Opening | Quarterly change | Ending | Source of change |
|---|---:|---:|---:|---|
| Cash | 50 | +13 | 63 | CFO 6 + CFI (−8) + CFF 15 |
| Accounts receivable | 0 | +20 | 20 | Credit sales |
| Inventory | 20 | +10 | 30 | Purchases 50 − COGS 40 |
| Net PP&E | 100 | −2 | 98 | Purchases 8 − depreciation 10 |
| Total assets | 170 | +41 | 211 | Sum of the four asset changes |
| Accounts payable | 0 | +10 | 10 | Supplier credit |
| Borrowing | 40 | +15 | 55 | New borrowing |
| Total liabilities | 40 | +25 | 65 | AP and borrowing |
| Equity | 130 | +16 | 146 | Net income 16, no dividends or share issues |
| Total liabilities and equity | 170 | +41 | 211 | Ending balance-sheet identity holds |

The statements answer different questions. The income statement explains accounting performance during the period; the balance sheet lists unsettled resources and obligations at the ending date; the cash flow statement explains cash rising from 50 to 63. Net income 16 enters retained earnings within equity, with no dividends or share issues here. Equipment purchases first increase assets and reduce cash; later depreciation reduces profit and net equipment value over time. Borrowing creates cash and debt, not revenue. Under this chapter's definition, $FCF=6-8=-2$. This deducts only the specified PP&E expenditure, not debt principal, dividends, acquisitions, or lease payments, and is not cash unconditionally distributable to shareholders.

:::

All figures above are constructed for teaching. The SEC investor guide also introduces the three statements through these questions and describes indirect CFO as net-income adjustments for noncash items and changes in operating assets and liabilities. [SEC Beginners’ Guide to Financial Statements](https://www.sec.gov/reportspubs/investor-publications/investorpubsbegfinstmtguide)

## 4. Mathematical Foundations

Start financial-statement formulas by checking dimensions.

- Income-statement and cash-flow items are flows over a period, such as FY2024 net sales and CFO.
- Balance-sheet items are stocks at a date, such as cash, debt, and receivables on 2024-09-28.
- Amounts must share a currency and unit. A value of 118,254 in USD millions differs numerically from 118,254,000 in USD thousands; the bare number is insufficient.
- Ratios are usually dimensionless. Dividing one amount by another still requires compatible periods, currencies, and units.
- Fiscal years need not equal calendar years. Apple FY2024 ends on 2024-09-28 and FY2023 on 2023-09-30; neither is a calendar year ending December 31.

A feature table can represent a fact by the tuple \((i,p,v,x,u,a)\): \(i\) is a permanent issuer or entity identifier, \(p\) the reporting period or instant, \(v\) the document version, \(x\) the value, \(u\) the currency and unit, and \(a\) its information-availability time. Also record local ingestion time \(g\), statement name, line name, source URL, accession, and processing-code version. These fields let two researchers determine whether they calculated the same quantity.

## 5. Formal Definitions

The **income statement** summarizes revenue, expenses, and profit over a period; the **balance sheet** summarizes assets, liabilities, and equity at a date; the **cash flow statement** summarizes operating, investing, and financing effects on cash and cash equivalents over a period. SEC guidance on reading a 10-K places audited financial statements in the annual report's financial-information section. Individual items still require the company's notes and audited statements. [How to Read a 10-K](https://www.sec.gov/files/reada10k.pdf)

The balance-sheet identity is:

\[
\text{Assets}_{t}=\text{Liabilities}_{t}+\text{Equity}_{t}.
\]

Here \(t\) is the closing date, not a period. Assets, Liabilities, and Equity are totals within the same consolidation scope. If NCI is presented within equity, Equity on the right includes it. A common-shareholder factor must instead match equity and earnings attributable to the parent's common shareholders.

This chapter reconciles the cash flow statement as follows:

\[
\text{Cash}_{t_1}-\text{Cash}_{t_0}
=\text{CFO}+\text{CFI}+\text{CFF}+\text{FX}.
\]

\(t_0,t_1\) are the opening and closing instants of the reporting period. CFO, CFI, and CFF are operating, investing, and financing cash flows; FX separately reconciles exchange-rate effects on cash and cash equivalents. Actual statements may differ in their coverage of cash, cash equivalents, restricted cash, and exchange adjustments: use the statement's own definition. IAS 7 also organizes cash flows into operating, investing, and financing activities and presents exchange-rate effects separately from those flows. [IAS 7.11 and 7.28](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias7.html)

Revenue is a period item recognized under the reporting entity's applicable standards and contractual facts. Revenue growth is often written as:

\[
g_t=\frac{R_t}{R_{t-1}}-1,
\]

\(R_t\) and \(R_{t-1}\) are revenues for the same company, currency, unit, comparable fiscal periods, and consistent version snapshot; \(g_t\) is a dimensionless growth rate. Differences in fiscal weeks, acquisition scope, exchange rates, or revenue-recognition versions may leave the rate computable without representing the same economic change.

**Operating income** generally subtracts operating costs and expenses from operating revenue. Presentation and classification of restructuring or unusual items differ across companies. **EBIT** can approximate operating income, but the terms are not interchangeable in every statement. Declare the original line used rather than storing only the label “EBIT.”

Analysts often construct **EBITDA** as:

\[
\text{EBITDA}^{*}_t=\text{EBIT}^{*}_t+\text{D\&A}_t.
\]

In the code, \(\text{EBIT}^{*}\) uses operating income and \(\text{D\&A}\) is D&A for the same period. The asterisk marks a teaching proxy. Company-reported Adjusted EBITDA may additionally exclude share-based compensation, restructuring charges, impairments, or acquisition amortization; this formula does not equal that disclosed adjusted measure.

**Net income** is the accounting result after applicable expenses, taxes, and other gains and losses. Consolidated net income may include profit attributable to NCI. For a factor representing the parent's common shareholders, select the profit line attributable to the parent or common shareholders. IAS 1 requires separate presentation of profit and comprehensive income attributable to parent owners and NCI. [IAS 1.81A and 1.106(a)](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ias1.html)

**Cash flow from operations (CFO)** is net operating cash inflow over the reporting period. The indirect method usually begins with net income or loss, reverses noncash items, and adjusts for cash effects of operating assets and liabilities. CFO therefore equals neither net income nor EBITDA.

**Capital expenditure (CapEx)** here means cash spent on the specified PP&E purchases during the reporting period. Statements often report it as a negative investing cash flow. Convert expenditure to a positive amount for the formula:

\[
\text{CapEx}_t=-\text{PP\&E cash-flow line}_t \quad \text{(when the line is nonpositive cash flow)}.
\]

Software development, capitalized R&D, leases, intangibles, and acquisitions classified as investing by a company are not automatically included in this CapEx definition.

::: {.body-definition title="Definition and Conditions: This Chapter’s CFO-minus-CapEx Proxy"}

This chapter explicitly defines **free cash flow (FCF)** as:

\[
\text{FCF}_t=\text{CFO}_t-\text{CapEx}_t
=\text{CFO}_t+\text{PP\&E cash-flow line}_t.
\]

\(\text{CFO}_t\) and \(\text{CapEx}_t\) must share the same period, currency, unit, and statement version. The first is signed net operating cash flow; the second is positive capital expenditure. SEC staff identifies CFO minus capital expenditures as a common FCF calculation while noting that FCF lacks a uniform definition. Readers must not be led to believe it deducts all debt service and other nondiscretionary spending. [SEC Non-GAAP C&DI 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures)

:::

**Working capital (WC)** has no single factor definition. To specify this chapter's scope, define the following six-item **Selected Operating Working Capital (Selected OWC)**. It is a reproducible subset of operating working capital, not complete working capital or complete net working capital:

\[
\text{Selected OWC}_t
=\text{AR}_t+\text{VendorRec}_t+\text{Inventory}_t+\text{OtherOpCA}_t
-\text{AP}_t-\text{DeferredRevenue}_t.
\]

\(\text{AR}\) is AR, \(\text{VendorRec}\) vendor non-trade receivables, \(\text{Inventory}\) inventory, \(\text{OtherOpCA}\) other current operating assets included here, \(\text{AP}\) AP, and \(\text{DeferredRevenue}\) deferred revenue liabilities. This excludes cash, security investments, borrowings, and other current liabilities. A full working-capital definition may cover other accounts; this Selected OWC subset is not a universal net-working-capital measure.

A simplified indirect method is:

\[
\text{CFO}_t\approx \text{NI}_t+\text{Noncash}_t-\Delta \text{OWC}_t+\text{OtherAdj}_t.
\]

\(\text{NI}\) is net income; \(\text{Noncash}\) adjusts for noncash expenses such as depreciation less noncash gains; \(\Delta\text{OWC}=\text{OWC}_{t_1}-\text{OWC}_{t_0}\); and \(\text{OtherAdj}\) includes other adjustments, tax/interest classification, noncurrent operating items, exchange effects, or acquisition effects. The approximation sign matters: a selected balance-sheet subset may not reproduce the full movements across the larger set of accounts in the statement's CFO reconciliation.

Limit **debt** to explicitly defined interest-bearing financing items. The Apple example uses commercial paper and current and noncurrent term debt. Define net debt as:

\[
\text{NetDebt}_t=\text{InterestBearingDebt}_t-\text{CashAndEquivalents}_t.
\]

This formula does not deduct marketable securities or include lease liabilities, and it is not every industry's definition of net financial liabilities. When the EBITDA proxy is nonpositive, NetDebt/EBITDA lacks the interpretation adopted here; the code returns an undefined value rather than forcing an ordinary ratio.

A **factor** here is a cross-sectional or time-series feature obtained through an explicit transformation of financial facts, such as gross margin, CFO margin, FCF margin, net debt/EBITDA, or FCF yield. It defines a candidate signal, without automatically establishing expected returns, a causal mechanism, or a tradable strategy.

## 6. Derivations

### 6.1 Why the Statements Connect

A simplified equity roll-forward is:

\[
\text{Equity}_{t_1}\approx \text{Equity}_{t_0}+\text{NetIncome}_t-\text{Distributions}_t+\text{OtherEquityChanges}_t.
\]

\(\text{Distributions}\) denotes dividends or other distributions. The equity presentation of repurchases depends on standards and statement classification. Other equity changes include other comprehensive income, share issuance, currency translation, NCI, and accounting adjustments. Ending equity does not simply equal opening equity plus net income.

Indirect CFO starts from income-statement net income: the first link. CapEx is the second: equipment purchases increase PP&E and reduce balance-sheet cash, appear as investing outflows, and subsequently affect profit through depreciation. Borrowing is the third: proceeds increase cash and debt without increasing revenue; repayment reduces cash and debt, while principal repayment is not an operating expense.

These links explain how a business can simultaneously report positive net income, negative CFO, positive CapEx expenditure, and negative FCF. They answer different questions about accounting earnings, operating funding needs, investment intensity, and operating cash after defined CapEx.

### 6.2 From Profit to Cash

With simplified operating accounts, increases in AR and inventory consume cash; increases in AP and deferred revenue temporarily supply cash:

\[
\begin{aligned}
\text{CFO}_t\approx{}&\text{NI}_t+\text{D\&A}_t-\Delta\text{AR}_t-\Delta\text{VendorRec}_t\\
&-\Delta\text{Inventory}_t-\Delta\text{OtherOpCA}_t\\
&+\Delta\text{AP}_t+\Delta\text{DeferredRevenue}_t+\text{OtherAdj}_t.
\end{aligned}
\]

The equation connects a period flow to changes between endpoint stocks. Each \(\Delta X_t\) is ending less opening balance. Positive operating-asset changes enter approximate CFO negatively; positive operating-liability changes enter positively. It assumes selected changes correspond to the relevant cash receipts and payments. Actual statements include allowances, exchange effects, acquisitions, disposals, noncurrent items, and reclassifications; this is not a company's complete indirect reconciliation.

The six changes explicitly match Selected OWC. OtherAdj excludes these six cash changes and contains only other adjustments. Ignoring or separately adjusting the noncash differences above, their working-capital changes combine into \(-\Delta\text{Selected OWC}\). Once CFO includes that movement, deducting the same \(\Delta\text{Selected OWC}\) again is a double deduction. To construct CFO excluding working-capital movements, state exactly which changes are added back or removed and reconcile them individually.

### 6.3 From Statement Items to Candidate Factors

Operating margin, net margin, and CFO margin describe operating profit, final accounting earnings attributable to a specified entity, and operating cash relative to revenue, respectively. Typical ratios are:

\[
\begin{aligned}
\text{OperatingMargin}_t&=\frac{\text{OperatingIncome}_t}{\text{Revenue}_t},\\
\text{NIMargin}_t&=\frac{\text{NetIncome}_t}{\text{Revenue}_t},\\
\text{CFOMargin}_t&=\frac{\text{CFO}_t}{\text{Revenue}_t}.
\end{aligned}
\]

Operating-margin and CFO-margin amounts must cover the same consolidation scope and fiscal period, currency, and unit. Net margin also requires an attribution convention: the equation above uses consolidated net income and consolidated revenue. For net margin attributable to the parent, this chapter divides parent-attributable net income by consolidated revenue for the same group and period. This revenue-denominator convention differs from matching common earnings to common equity for ROE or common market capitalization for P/E. Do not mechanically allocate revenue by ownership percentage to invent undefined “common-shareholder revenue.” Negative net income still expresses a loss relative to the declared revenue base. With nonpositive revenue, these margins lose their ordinary business interpretation.

FCF margin and FCF yield use different denominators. For cross-company annual yield comparisons, use consistent annual or trailing-twelve-month (TTM) FCF. Label a quarterly window separately rather than treating it as annualized. A fixed window makes rankings reflect financial differences instead of differing measurement lengths:

\[
\text{FCFMargin}_t=\frac{\text{FCF}_t}{\text{Revenue}_t},\qquad
\text{FCFYield}_{s,t}=\frac{\text{FCF}_{i,p,v}}{\text{MarketCapitalization}_{s,t}}.
\]

\(i,p,v\) identifies the company, reporting period, and selected statement version; \(s,t\) identifies the security and market-valuation time. Yield divides period FCF from a known version by equity market capitalization at signal time, in comparable currency and units. Do not backfill the denominator with future prices or share counts. FCF yield is also not an enterprise-value yield. Chapter 13 examines EV versus equity scope.

Asset-efficiency ratios often divide a period flow by an average stock, for example:

\[
\text{ROA}_t=\frac{\text{NetIncome}_t}{(\text{Assets}_{t_0}+\text{Assets}_{t_1})/2}.
\]

\(\text{ROA}\) is the simple net-income/average-total-assets definition shown here. Other studies may use operating income, after-tax operating profit, or another numerator. Average assets match period flows with average resources; using only an ending balance changes the denominator to an ending-stock measure. Both prior and current statement values must come from versions visible at signal time.

### 6.4 Deriving Version and Availability Rules

::: {.body-conditions title="Conditions: Two Clocks and Independent Validity"}

For candidate version \(v\) and signal time \(s\), this simplified demonstration checks two availability clocks, assuming no withdrawal or non-reliance event:

\[
\operatorname{eligible}(v,s)
\iff a_v\leq s\ \land\ g_v\leq s.
\]

\(a_v\) is when the value first became public or that version became a public source; \(g_v\) is when the research pipeline confirmed receipt and made it usable by this research run; \(s\) is the signal-generation cutoff. Both clocks are necessary. A public document absent from this research database was not readable by this backtest instance then. A prerelease field ingested before publication cannot inform a market signal early either.

Among available versions, select the one with the latest source-publication time:

\[
v^*(s)=\arg\max_{v:\ \operatorname{eligible}(v,s)} a_v.
\]

Sort by \(a_v\), not ingestion time \(g_v\). An older report ingested late must not obscure a newer report ingested on time. A revision replaces nothing before both its publication and ingestion. Conflicting rows for the same company, period, and source-availability time require stopping to resolve the version key, rather than letting file order select the value.

This is only a two-clock selector, not a complete statement-validity system. A withdrawal or non-reliance notice can change an old value's research eligibility without supplying a new number. Production selection also needs an event-time validity state \(h_v(s)\): 1 means the version remains eligible for the defined research at the signal cutoff, based on status events already public and ingested; 0 means withdrawn or marked non-reliable. Full eligibility includes \(a_v\le s\), \(g_v\le s\), and \(h_v(s)=1\). Status events need their own source versions and publication/ingestion times. A notice learned later must not be backfilled into an earlier cutoff.

After Spire's non-reliance notice became visible to the research system but before an eligible restatement arrived, “latest available number” would not justify continued use of an invalid original. Mark the feature unavailable and follow a predefined missing-data policy to exclude, pause, or flag it for review. Do not fill the gap with the unpublished 2025 restatement. This chapter's code has no withdrawal-event interface or complete company status timeline. Its constructed two-clock example does not cover that real intermediate window and cannot establish historical tradable signals for Spire.

:::

Real records often establish only a date, without precise publication time or time zone. Preserve date precision instead of inventing midnight UTC. Apple FY2024 10-K headers give period of report 2024-09-28, filed date 2024-11-01, and raw acceptance string 20241101060136; Apple's newsroom dates the FY2024 release 2024-10-31. Spire's original FY2023 period ends 2023-12-31, with filing on 2024-03-06, an August 2024 non-reliance notice for certain historical statements, and a 10-K/A filed 2025-03-03. The acceptance strings are not converted into a trading time zone here, and local vendor ingestion records are unavailable. [Apple EDGAR headers](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index-headers.html), [Spire original headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/0000950170-24-027164-index-headers.html), [Spire restatement 10-K/A](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm)

## 7. Financial Interpretation

Statement items describe accounting recognition; researchers then choose how to measure economic phenomena. Revenue growth measures recognized sales growth, not customer payment timing. Margins measure a profit level relative to revenue, not cash after fixed-asset replacement, debt principal, and shareholder distributions. CFO represents reported operating cash, without deducting every investment need. FCF interpretation depends on the statement and CapEx definition.

Common quality-factor intuitions ask whether profit converts to cash, assets turn over quickly, or debt increases financial fragility. Candidate measures include CFO/NetIncome, CFO/Revenue, ROA, and net debt/EBITDA. These remain measurement choices. Near-zero net income magnifies CFO/NetIncome; negative EBITDA makes net debt/EBITDA hard to interpret; low FCF during rapid capacity construction may indicate investment rather than deteriorating operations.

Working-capital changes have multiple interpretations. AR growing faster than revenue may indicate slower collection, quarter-end shipments, or a changing business mix. Delaying suppliers temporarily raises CFO, but payment terms and sustainability also matter. Strong seasonality can confound annual endpoint changes; quarterly comparisons need matching quarters and fiscal weeks.

Debt measures must match the equity entity. Gross interest-bearing debt, cash offsets, lease liabilities, supply-chain finance, and NCI may change leverage or valuation scope. Deducting illiquid restricted cash or omitting debt is not repaired by retaining the name NetDebt. Store the formula version and included account list.

**Noncontrolling interest (NCI)** sharpens the distinction between group net income and earnings attributable to the parent's common shareholders. Consolidating a subsidiary without owning all its equity includes amounts attributable to outside holders in consolidated profit and balance-sheet totals. Common-equity profitability and market multiples require numerators and denominators for the same equity holders. IAS 1 presents parent-owner and NCI attribution separately. [IAS 1](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ias1.html)

Accounting differences also affect international samples. Interest, dividends, and certain cash-flow classifications may vary by standard and period; presentation of revenue, leases, and development expenditure can differ too. Uniform English field names do not erase these differences. Preserve original labels, standards, company extensions, accounting policies, years, and revision status.

## 8. Numerical Example

### 8.1 Three-Statement Hand Calculation: A Constructed Company

Section 3, this section, and 12-E07/12-L06 use the same fictional company, quarter, and constructed unit $u$, allowing line-by-line recalculation. The income statement is:

\[
\text{GrossProfit}=100-40=60,\quad
\text{EBIT}^{*}=60-25-10=25,\quad
\text{NetIncome}=25-5-4=16.
\]

Revenue, COGS, cash operating expenses, depreciation, interest, and tax are constructed period amounts. Operating income approximates EBIT; other nonoperating items are excluded.

With opening operating assets of inventory 20 and ending AR 20, inventory 30, and AP 10, Selected OWC rises from \(20\) to \(20+30-10=40\), an increase of \(20\). Begin with net income \(16\), add noncash depreciation \(10\), deduct AR and inventory increases \(20+10\), and add AP growth \(10\) to obtain CFO \(6\). A quick check is \(\text{NI}+\text{D\&A}-\Delta\text{OWC}=16+10-20=6\).

CapEx \(8\) is positive expenditure; the PP&E cash-flow line records \(-8\). This chapter's FCF is therefore \(6-8=-2\). With new borrowing 15, opening cash 50, and no other cash flows, ending cash is \(50+6-8+15=63\).

Ending assets are cash 63, AR 20, inventory 30, and net PP&E \(100+8-10=98\), totaling 211. Liabilities are AP 10 and debt \(40+15=55\); equity rises from 130 by net income 16 to 146, also totaling 211 on the right. Equipment purchases of 8 first enter assets; depreciation of 10 reduces book PP&E through expense. Cash payment and current-period depreciation differ.

### 8.2 Apple FY2024 and FY2023: Recalculating Original Statement Figures

Apple's 2024 Form 10-K consolidated cash flow statement uses USD millions. For FY2024 (ending 2024-09-28) and FY2023 (ending 2023-09-30), Cash generated by operating activities is 118,254 and 110,543; Payments for acquisition of property, plant and equipment is −9,447 and −10,959. Convert the negative lines into positive CapEx expenditure:

\[
\text{FCF}_{2024}=118{,}254-9{,}447=108{,}807,
\qquad
\text{FCF}_{2023}=110{,}543-10{,}959=99{,}584
\]

All amounts are USD millions. Year-over-year FCF growth is \(108{,}807/99{,}584-1\approx9.26\%\). This year-over-year change in FCF is neither a stock return nor sufficient evidence of a sustained improvement in cash generation.

Net sales in the same 10-K are 391,035 and 383,285, growing approximately \(2.0220\%\). FY2024 gross profit is 180,683, giving gross margin \(180{,}683/391{,}035\approx46.21\%\). Operating income of 123,216 gives operating margin approximately \(31.51\%\). D&A of 11,445 produces the teaching EBITDA proxy \(123{,}216+11{,}445=134{,}661\), not an Apple-announced adjusted EBITDA.

Under this chapter's debt definition, FY2024 interest-bearing debt is commercial paper 9,967 plus current term debt 10,912 plus noncurrent term debt 85,750, totaling 106,629. Deduct only cash and cash equivalents 29,943 to obtain net debt 76,686 USD millions. Marketable securities and lease liabilities are outside this narrow definition. The statement supplies no matched historical market-capitalization input for this example. The FCF-yield code separately constructs market capitalization of 4,000,000 USD millions solely to demonstrate same-unit division. Do not report 2.72% as Apple's actual FCF yield.

### 8.3 Spire FY2023: Original and Restated Versions

::: {.body-example title="Worked Example: Two Versions of Annual FCF and Their Limits"}

Spire's original FY2023 Form 10-K (accession 0000950170-24-027164) reports CFO \(-23{,}622\) and PP&E purchase cash flow \(-30{,}037\) in USD thousands. Convert to positive CapEx expenditure \(30{,}037\):

\[
\text{FCF}_{\mathrm{original}}
=-23{,}622-30{,}037=-53{,}659\ \text{USD thousands}.
\]

Spire's 2025 Form 10-K/A (accession 0000950170-25-030856) restates that same FY2023 with CFO \(-36{,}307\) and PP&E purchase cash flow \(-17{,}352\). Thus:

\[
\text{FCF}_{\mathrm{restated}}
=-36{,}307-17{,}352=-53{,}659\ \text{USD thousands}.
\]

Under this defined formula, FCF happens to be unchanged: the 12,685 downward CFO revision offsets the 12,685 reduction in CapEx expenditure. Spire's restatement materials explain how contract revenue and cost recognition, leases, customer notes, and other accounting matters affect multiple periods and statements. Two cash-flow lines alone miss those version changes. This single case cannot establish that other restatements must offset. [Original 10-K](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/spir-20231231.htm), [10-K/A](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm)

:::

## 9. Python Implementation

### Default Entry Point for This Reader Edition

From the accepted I3 reader package root, set up the environment using its [instructions](../../README.md), then run:

```bash
.venv/bin/python run_notebook.py notebooks/ch12_statements.ipynb
```

The Notebook calls the packaged shared implementation. Chapter 12 recalculates fixed transcriptions of Apple/Spire statement facts; PIT clocks and market capitalization are constructed. By default it displays the two existing packaged figures without redrawing them. The runner writes new kernel execution records to a unique `runs/execution_*` directory; the Notebook separately creates a unique UUID chapter-method directory and prints its location. These directories serve different purposes, and existing figures are not new outputs from this batch. French data absent from the package are neither read by default nor downloaded. The CLI and old production tests below refer to the working-course root. Readers use the Notebook assertions above and need not restore unbundled production tests. The English Notebook Markdown layer remains pending BIL23 integration. This batch executed neither Notebooks nor old numerical suites.

### Historical Working-Course Root and Original Implementation

Core metric and version functions are in [statement_metrics.py](../../../../src/quant_course/statement_metrics.py); CLI and plotting entry points are in [ch12_statements.py](../../../../code/ch12_statements.py); program tests are in test_ch12_statements.py; and the teaching Notebook is [ch12_statements.ipynb](../../../../notebooks/ch12_statements.ipynb). The core module records each FinancialFact's entity, period, currency, unit, accession, revision status, and source. FCF requires CFO and the PP&E expenditure line from the same version and rejects positive “outflow” inputs. Feature functions also check unit/version mismatches, nonfinite values, basic statement reconciliations, and CapEx signs.

Run from the project root:

```text
.venv/bin/python code/ch12_statements.py
.venv/bin/python -m pytest tests/test_ch12_statements.py -q
```

The code neither downloads statements nor connects to market quotes. Apple and Spire inputs are fixed transcriptions of selected source figures. Running the example generates the two chapter figures. The following call can run independently in the project virtual environment:

```python
import math
import sys

from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.statement_metrics import (
    apple_facts,
    derive_accounting_factors,
    fcf_from_statement_lines,
    fcf_yield,
    spire_cash_flow_facts,
)

apple_2024 = derive_accounting_factors(apple_facts(2024))
assert apple_2024["fcf"] == 108_807.0
constructed_yield = fcf_yield(
    apple_2024["fcf"],
    4_000_000.0,
    currency="USD",
    statement_unit="USD millions",
    market_cap_currency="USD",
    market_cap_unit="USD millions",
    market_cap_label="constructed teaching value",
)
assert math.isclose(constructed_yield, 0.02720175, rel_tol=0, abs_tol=1e-8)

for version in ("original", "restated"):
    cfo, capex_cash_flow = spire_cash_flow_facts(version)
    print(version, fcf_from_statement_lines(cfo, capex_cash_flow))
```

Reporting frequency above is annual; FY2024/FY2023 follow Apple's fiscal years, not calendar years. A date-only financial signal timestamp cannot establish intraday availability; actual receipt and ingestion times still require external logs. The PIT helper uses explicitly SIM-labeled constructed UTC times and selects only versions whose available_at and ingested_at do not exceed signal_time. Trading must follow information arrival and strategy processing, with execution latency handled as in Chapters 3 and 29. This chapter estimates no return interval.

This chapter's `FinancialFact` is a minimal teaching structure for these transcriptions. It labels fiscal years with `fiscal_period` but does not explicitly distinguish period flows from closing-date stocks or separately store `period_start`, `period_end`, or `as_of_date`. Production panels should preserve flow start/end dates, stock closing/effective instants, and `fact_period_type`. This lightweight class is not a complete financial-data schema.

## 10. Visualization

![Apple cash flows and chapter-defined FCF for two fiscal years](../../../../figures/a3/ch12_apple_cashflow.png)

The [Apple FY2023/FY2024 CFO, CapEx, and FCF figure](../../../../figures/a3/ch12_apple_cashflow.png) uses fiscal years horizontally and USD millions vertically. Blue bars show CFO; orange bars convert negative PP&E purchase cash flows into positive CapEx expenditure; green bars calculate CFO−CapEx. This displays two reporting years and their units, not stock prices or factor returns. FY2024 CFO and defined FCF are higher, while CapEx expenditure is lower. The chart alone does not explain why.

![Two statement versions for the same Spire fiscal year](../../../../figures/a3/ch12_spire_revision.png)

The [Spire FY2023 original-versus-restated figure](../../../../figures/a3/ch12_spire_revision.png) fixes the reporting period, changes document version horizontally, and uses USD thousands vertically. Blue CFO and green FCF lie below zero; orange CapEx is positive expenditure. Restated CFO is more negative and CapEx expenditure smaller, while chapter-defined FCF remains −53,659. Check accession numbers and signs before discussing whether a measure changed.

Figure text identifies original documents, versions, and this chapter's FCF formula. Real figures come only from the relevant SEC statements; they contain no actual stock prices, vendor timestamps, or investment performance.

## 11. Real Market Example

This section uses actual public statements to test limited claims. These are neither complete security-level PIT data nor empirical strategy evidence.

Apple FY2024 10-K headers list period of report 2024-09-28, filed as of date 2024-11-01, and raw acceptance 20241101060136. Apple's newsroom dates the fourth-quarter/full-year FY2024 announcement 2024-10-31. The filing presents adjacent audited FY2024/FY2023 statements. Under the specified lines and definition, FCF is 108,807 and 99,584 USD millions. This establishes that the document version follows period-end and permits recalculation of two fiscal years. These pages alone do not establish the release's precise publication time, when a vendor received the full text, or when all 10-K notes became market-visible that day.

Spire's original FY2023 10-K has period-end 2023-12-31, accession 0000950170-24-027164, and filed date 2024-03-06. A subsequent Form 8-K states that certain issued statements should no longer be relied upon and require restatement. Its headers distinguish report date 2024-08-21, filed date 2024-08-27, and raw acceptance 20240827161154. On 2025-03-03 the company filed 10-K/A accession 0000950170-25-030856 with restated FY2023 statements. The three document versions remain separate; 2025 numbers do not replace original features generated in March 2024.

The company IR page provides a FY2023 results-announcement date of 2024-03-05, but its precise publication time zone was not verified here. Neither 10-K acceptance field is converted to UTC. These companies provide statement/version facts, without historical vendor ingestion logs, exchange calendars, security prices at trading instants, historical shares outstanding, delisted securities, or complete permanent-ID mappings required by this research. Thus no historical Apple or Spire FCF yield, validated PIT factor, or actual market regression is reported.

SEC companyfacts and frames facilitate XBRL retrieval. Frames organizes recent matching filing facts around a specified calendar period, while corporate fiscal years may not align. Current API results do not automatically replace historical snapshots preserving original accession numbers and version chains. [SEC EDGAR API documentation](https://www.sec.gov/edgar/sec-api-documentation)

## 12. Common Mistakes

**Treating report period-end as availability.** Putting Spire's December 31 figures into the December 31 closing signal is wrong. Period-end describes measurement; first publication requires release records and research receipt requires ingestion logs. Preserve separate time fields and filter at a verifiable signal cutoff.

**Collapsing filed date, acceptance, and ingestion into one timestamp.** SEC accession headers show different metadata for period, filing date, and raw acceptance, without recording local database receipt. Preserve each raw field, its time-zone status, and system receipt logs; mark missing information unknown.

::: {.body-pitfall title="Pitfall: Negative Cash-Flow Lines versus Positive Expenditure"}

**Subtracting a negative CapEx line again.** Apple FY2024 PP&E cash flow is −9,447, while CapEx expenditure is +9,447. The wrong calculation is \(118{,}254-(-9{,}447)=127{,}701\); the correct one is \(118{,}254-9{,}447=108{,}807\). For inputs recorded as negative outflows, this is equivalently CFO plus that negative line.

```python
cfo = 118_254.0
reported_ppe_cash_flow = -9_447.0
wrong = cfo - reported_ppe_cash_flow       # 127,701, sign error
capex_spend = -reported_ppe_cash_flow
correct = cfo - capex_spend                # 108,807
assert wrong == 127_701.0
assert correct == 108_807.0
```

:::

**Deducting the same working-capital changes again after CFO.** The teaching company's CFO of 6 already includes AR, inventory, and AP movements. FCF is \(6-8=-2\). Deducting working-capital growth 20 again gives −22, double-counting the cash use. To estimate CFO excluding a particular working-capital change, identify that same item's cash contribution in the full reconciliation and specify its removal or add-back. Do not automatically adjust again using a different balance-sheet proxy.

**Calling FCF a uniform GAAP line or freely spendable cash.** This formula deducts only selected PP&E CapEx from CFO, not principal repayments, dividends, acquisitions, lease payments, or other potentially necessary investment. Different research may use different CapEx coverage: preserve formula versions and included line names.

**Allowing later restatements to rewrite past samples.** CFO −36,307 in Spire's 2025 10-K/A and original CFO −23,622 are different versions. Using the 2025 value for an early-2024 signal embeds information absent then. Filter version metadata with both clocks and preserve each accession.

**Treating frames output as calendar-year data or a historical vintage.** Fiscal year-end may differ from December; frames selects recent matching facts for a calendar period. Even after reading the SEC API documentation, check original filings and period contexts. A recent API response is not proof of what a system actually saw on a past date.

**Treating company facts directly as stock signals.** A company may have common stock, multiple share classes, ADRs, predecessor entities, or delisted securities. CIK and ticker alone do not map every field to a tradable share class. Build a historical issuer/security mapping with permanent identifiers and specify per-share or equity-level denominators.

## 13. Quant Research Application

Start with a falsifiable hypothesis, such as: “Do companies with high CFO margin, measured using aligned fiscal years and public versions, subsequently have different cross-sectional returns from low-CFO-margin companies?” This remains a research question; two company cases cannot answer it.

First define the universe and measurement. Choose CFO/Revenue, CFO/average assets, or CFO/Net Income; specify statement lines, matched currency/unit, fiscal periods, revenue-recognition versions, and missing-data treatment. For FCF, define the CapEx line and sign; for NetDebt/EBITDA, specify debt accounts and whether EBITDA is disclosed or a research proxy. Define null/group handling for nonpositive numerators or denominators.

Next build source and version tables. Link every raw fact to permanent issuer ID, period, accession, version status, document line, first verified publication time, SEC filed date, parsable accepted field, system ingestion time, and cleaning-code version. Do not label current companyfacts retrieval as a historical snapshot. Preserve custom XBRL tags, units, period contexts, and normalization rules. Resolve duplicate facts by duration/instant, currency, dimensions, and revision source.

Third, select PIT versions. Both available_at and ingested_at must be no later than the signal cutoff; choose the latest-published eligible version. Date-only timestamps require more conservative date-level cutoffs with explicit assumptions. Without market time zones and trading calendars, claim no intraday availability. Only then map issuer fields to securities, share classes, and markets existing at that time.

Fourth, ensure comparability. Compute revenue growth for aligned fiscal cycles, consolidation scopes, currencies, and version snapshots. Specify ending or period-average stock denominators. Preserve event flags for acquisitions, spin-offs, accounting-policy changes, currency conversion, and restatements. Distinguish not applicable, unreported, source unavailable, unpublished, and parsing failure instead of filling all with zero.

Fifth, define the research sample and baseline. Use the historical company universe knowable then, recording delistings and identifier changes; survivorship filters may alter the cross-section. Compare the feature with a simple baseline excluding it. Preregister winsorization, industry adjustment, standardization, holding period, and trading lag. Use chronological out-of-sample evaluation and results after transaction costs rather than choosing the best full-sample transformation.

Finally, seek counterevidence. If an advantage appears only in restated versions, requires zero-filled missing values, depends on mismatched fiscal years or excluding delisted firms, or vanishes at an executable post-announcement time, report those measurement and implementation boundaries. Without real historical data and complete PIT security mappings, the work establishes statement arithmetic and engineering demonstrations, not empirical factor results.

## 14. Chapter Summary

The three statements describe period earnings, ending resources and obligations, and cash sources and uses. Net income, operating accounts, depreciation, CapEx, and financing connect them. Before turning these items into a factor, specify numerator, denominator, period, entity, currency, and unit, preserving original line names and formulas.

CFO and net income measure different outcomes. Convert CapEx cash-flow signs consistently; FCF depends on the declared CapEx scope. Do not deduct a working-capital proxy again when CFO already includes the same change. Revenue margins, cash conversion, and debt ratios are comparable only with matched definitions, periods, and shareholder entities.

Historical statements also have versions. Period-end, first publication, filing date, accepted field, revision announcement, and ingestion are distinct time information. A version may generate a signal only after it is public and in the research system. Later versions belong at their actual future availability times.

## 15. Exercises

Reference answers to conceptual questions are in Section 18.

**12-E01 (Identify the statements)** Credit sales increase revenue and receivables before customers pay. Which statements change first, and why might indirect CFO be below net income?

**12-E02 (Levels of accounting profit)** Distinguish EBIT, the EBITDA proxy, net income, and CFO in one sentence. Which may correspond directly to statement lines, and which require construction or definition checks?

**12-E03 (Balance-sheet identity)** A company has assets 500, liabilities 360, shareholder equity 130, and NCI 10. Does the identity hold? Can NCI 10 enter parent equity in a parent-shareholder feature?

**12-E04 (Time fields)** A FY2023 statement has period-end 2023-12-31, SEC filed date 2024-03-06, and local ingestion 2024-03-08. When can it first inform a strategy signal? What timing evidence is missing?

**12-E05 (NWC and CFO)** AR and inventory rise while AP is unchanged. What are their directions in indirect CFO? Why is deducting those same changes again after CFO wrong?

**12-E06 (Shareholder scope)** Consolidated net income is 100, including 15 attributable to NCI. For parent common-shareholder profitability, should the simple net-margin numerator be 100 or 85? Explain which definitions the numerator's entity must match.

Show formulas, variables, and units in hand calculations.

**12-E07 (Three-statement links)** Using the same fictional company from Sections 3 and 8 (all amounts in constructed unit $u$), calculate gross profit, EBIT, net income, CFO, FCF, ending cash, and ending assets/liabilities/equity. Explain depreciation and credit sales at each step.

**12-E08 (Actual Apple statements)** Apple FY2024 CFO is 118,254, the PP&E cash-flow line −9,447, and revenue 391,035, all in USD millions. Calculate positive CapEx expenditure, FCF, FCF margin, and CFO margin.

**12-E09 (Spire versions)** Original CFO is −23,622 and the PP&E line −30,037; restated CFO is −36,307 and the PP&E line −17,352, in USD thousands. Calculate each FCF, identify changed items, and explain whether this establishes a uniform FCF definition.

## 16. Programming Exercises

Section 18 contains each programming exercise's inputs, error boundaries, and reference implementation. Code uses Python, pandas, and this chapter's module. Every demonstration timestamp is explicitly constructed.

**12-P01 (Sign- and unit-safe FCF)** Write a function taking CFO and a negative PP&E outflow line. Validate matching currency, unit, period, and accession, then return FCF. Acceptance: Apple FY2024 returns 108,807; changing CapEx to +9,447 or mismatching versions raises an exception.

**12-P02 (Two-clock PIT)** Test version selection with at least two constructed records for one company and fiscal year. The first is published before ingestion; the second is published and ingested after a signal. Add a signal between publication and ingestion. Require time-zone-aware timestamps and verify that late restatements do not overwrite early signals.

**12-P03 (Ratios and provenance)** Calculate FCF margin, operating margin, net debt/EBITDA proxy, and revenue growth from Apple FY2024 facts. Market capitalization may only be an explicitly constructed teaching input. Assert values and unit boundaries, including rejection of direct division of USD by USD millions.

## 17. Challenge Problems

Open questions can have multiple reasonable solutions, but answers must preserve assumptions, versions, and counterevidence.

**12-C01 (Restatement diagnosis; prerequisite: accounting reconciliations)** Spire restates CFO from −23,622 to −36,307 and PP&E cash expenditure from 30,037 to 17,352; net loss also changes. Chapter-defined FCF is unchanged. Give a bounded interpretation and list at least four statements or notes to check before attributing the changes to economic cash movements, reclassification, revenue recognition, capitalization, or other causes.

**12-C02 (PIT factor-data design; prerequisite: Chapter 3 data engineering)** Design a minimal auditable data model for cross-company annual FCF yield. Specify fields for raw facts, versions, availability, ingestion, issuer/security mapping, market-value sources, and feature derivation. Explain conservative treatment of report dates/filing acceptance without precise verified time zones, and give two counterevidence tests that could invalidate the factor.

## 18. Solutions / Solution Hints

### Conceptual Answers

**12-E01** The income statement and balance sheet change first. If recognition conditions are met, revenue rises, AR increases, and profit rolls into equity. Cash is uncollected, so indirect CFO starts from net income and deducts the AR increase as a cash use; CFO can be below net income. Recognition timing still depends on applicable standards and contractual performance facts.

**12-E02** EBIT is profit before interest and income tax, often approximated by operating income; the EBITDA proxy adds D&A to EBIT; net income further reflects interest, taxes, and other gains/losses; CFO adjusts net income to operating cash. Operating income and net income are usually reported lines, whose names, entities, and presentation require original-statement checks. Researcher-constructed EBIT+D&A must be labeled a proxy; company adjusted EBITDA differs from this formula. CFO is a cash-flow statement item with statement-specific coverage.

**12-E03** Liabilities plus equity are \(360+130+10=500\), exactly equal to assets. NCI 10 is part of consolidated equity; parent equity is 130, excluding NCI. Profit and valuation must follow the same entity convention.

**12-E04** These fields alone cannot establish the earliest usable instant. 2023-12-31 is period-end, 2024-03-06 is filed date, and local ingestion occurs only on 2024-03-08. Verify first public announcement or other available_at evidence. This research instance must at least wait for ingestion, so candidate signals require \(\max(\text{available\_at},\text{ingested\_at})\leq\text{signal\_time}\). Date-only times support only date-level conclusions.

**12-E05** AR and inventory are operating assets whose increases normally consume CFO; unchanged AP provides no cash offset from AP movements. Indirect CFO already adjusts net income for these changes. Deducting them again double-counts the cash use.

**12-E06** Consolidated net income 100 less NCI-attributable profit 15 gives parent-attributable net income 85. Only with the additional assumption of no preferred dividends or other distributions requiring deduction is 85 also earnings available to common shareholders. Otherwise bridge further from parent to common earnings. Under Section 6.3, parent-attributable net margin divides parent net income by consolidated revenue for the same group and period. No revenue is supplied here, so select the earnings numerator without reporting a numerical margin. There is no directly ownership-allocated “common-shareholder revenue” line. ROE pairs common earnings with common equity, specifying average or ending equity; P/E divides common market capitalization by common earnings. Consolidated net income 100 still describes the group but includes NCI profit 15.

### Hand-Calculation Answers

**12-E07** All amounts use constructed unit $u$. Revenue 100 less COGS 40 gives gross profit 60. Deduct cash operating expenses 25 and depreciation 10 for EBIT proxy 25, then interest 5 and tax 4 for net income 16. CFO starts at 16, adds noncash depreciation 10, deducts AR growth 20 and inventory growth 10, and adds AP growth 10, giving 6. CapEx expenditure is 8, so FCF = 6−8 = −2. Ending cash is 50+6−8+15 = 63. Assets are cash 63 + AR 20 + inventory 30 + net PP&E \(100+8−10=98\) = 211. Liabilities are AP 10 + debt 55 = 65. Equity is 130+net income 16 = 146, and 65+146=211. Credit sales create revenue and AR without current cash; depreciation reduces profit and equipment book value but is added back in CFO.

**12-E08** The PP&E line is a negative cash flow; positive CapEx = \(-(-9{,}447)=9{,}447\) USD millions. FCF = 118,254−9,447 = 108,807 USD millions. FCF margin = \(108{,}807/391{,}035\approx27.8254\%\); CFO margin = \(118{,}254/391{,}035\approx30.2413\%\). Both ratios are dimensionless. This is the chapter's FCF definition, not a standardized Apple GAAP line.

**12-E09** Original CapEx expenditure is 30,037, so FCF = −23,622−30,037=−53,659 USD thousands. Restated CapEx is 17,352, so FCF = −36,307−17,352=−53,659 USD thousands. CFO and CapEx each change by 12,685 in offsetting directions. This establishes only an offset under this definition, not uniform FCF definitions across companies or unchanged FCF in every restatement.

### Programming Reference Implementations

**12-P01** The following runs independently and explicitly preserves period, accession, currency, and unit. A positive CapEx outflow sign or mismatched version/period stops execution:

```python
from dataclasses import dataclass
from math import isclose, isfinite

@dataclass(frozen=True)
class Line:
    value: float
    period: str
    accession: str
    currency: str
    unit: str
    name: str

def same_frame(*lines: Line) -> None:
    keys = {(x.period, x.accession, x.currency, x.unit) for x in lines}
    if len(keys) != 1:
        raise ValueError("period, filing version, currency, and unit must match")
    if any(not isfinite(x.value) for x in lines):
        raise ValueError("line values must be finite")

def fcf(cfo: Line, capex_cash_flow: Line) -> float:
    same_frame(cfo, capex_cash_flow)
    if cfo.name != "cfo" or capex_cash_flow.name != "capex_cash_flow":
        raise ValueError("wrong line item")
    if capex_cash_flow.value > 0:
        raise ValueError("CapEx cash-flow line must be a non-positive outflow")
    return cfo.value - (-capex_cash_flow.value)

cfo = Line(118_254.0, "FY2024", "0000320193-24-000123", "USD", "millions", "cfo")
capex = Line(
    -9_447.0,
    "FY2024",
    "0000320193-24-000123",
    "USD",
    "millions",
    "capex_cash_flow",
)
assert fcf(cfo, capex) == 108_807.0
assert isclose(fcf(cfo, capex), 108_807.0, rel_tol=0, abs_tol=1e-12)

try:
    fcf(
        cfo,
        Line(
            9_447.0,
            "FY2024",
            cfo.accession,
            "USD",
            "millions",
            "capex_cash_flow",
        ),
    )
except ValueError:
    pass
else:
    raise AssertionError("positive cash outflow sign should fail")

try:
    fcf(
        cfo,
        Line(
            -9_447.0,
            "FY2024",
            "RESTATED-ACCESSION",
            "USD",
            "millions",
            "capex_cash_flow",
        ),
    )
except ValueError:
    pass
else:
    raise AssertionError("mixed filing versions should fail")
```

**12-P02** All dates and CFO values below are constructed; Z denotes explicitly specified UTC inputs. The project PIT join keeps the first version invisible at 14:15, after announcement but before ingestion. A restatement likewise cannot replace the original between its publication and ingestion:

```python
import sys
from pathlib import Path

import pandas as pd

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
from quant_course.pit import pit_asof_join

signals = pd.DataFrame({
    "issuer": ["SIM-1"] * 4,
    "period": ["FY2023"] * 4,
    "signal_time": [
        "2024-01-10T14:15:00Z",
        "2024-01-10T14:45:00Z",
        "2024-03-20T12:05:00Z",
        "2024-03-20T12:15:00Z",
    ],
})
versions = pd.DataFrame({
    "issuer": ["SIM-1", "SIM-1"],
    "period": ["FY2023", "FY2023"],
    "available_at": ["2024-01-10T14:00:00Z", "2024-03-20T12:00:00Z"],
    "ingested_at": ["2024-01-10T14:30:00Z", "2024-03-20T12:10:00Z"],
    "revision": ["original", "restated"],
    "cfo": [20.0, 14.0],
})
for frame, column in (
    (signals, "signal_time"),
    (versions, "available_at"),
    (versions, "ingested_at"),
):
    frame[column] = pd.to_datetime(frame[column], utc=True)
joined = pit_asof_join(
    signals, versions,
    security_col="issuer", period_col="period",
    signal_time_col="signal_time",
)
assert pd.isna(joined.loc[0, "cfo"])
assert joined.loc[1, "revision"] == "original"
assert joined.loc[2, "revision"] == "original"
assert joined.loc[3, "revision"] == "restated"
```

**12-P03** The chapter functions below validate Apple's source version. Market value is explicitly constructed. fcf_yield raises ValueError for currency or unit mismatches:

```python
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
from quant_course.statement_metrics import (
    apple_facts,
    derive_accounting_factors,
    fcf_yield,
    revenue_growth,
)

fy2024 = apple_facts(2024)
fy2023 = apple_facts(2023)
metrics = derive_accounting_factors(fy2024)
growth = revenue_growth(fy2024["revenue"], fy2023["revenue"])
assert metrics["fcf"] == 108_807.0
assert math.isclose(metrics["fcf_margin"], 108_807 / 391_035, abs_tol=1e-14)
assert math.isclose(metrics["operating_margin"], 123_216 / 391_035, abs_tol=1e-14)
assert math.isclose(growth, 391_035 / 383_285 - 1, abs_tol=1e-14)
assert math.isclose(
    metrics["net_debt_to_ebitda_proxy"], 76_686 / 134_661, abs_tol=1e-14
)
# Net debt and EBITDA use the same currency and unit; this ratio is dimensionless.

yield_demo = fcf_yield(
    metrics["fcf"], 4_000_000.0,
    currency="USD", statement_unit="USD millions",
    market_cap_currency="USD", market_cap_unit="USD millions",
    market_cap_label="constructed teaching market cap",
)
assert math.isclose(yield_demo, 108_807 / 4_000_000, abs_tol=1e-14)
try:
    fcf_yield(
        metrics["fcf"], 4_000_000.0,
        currency="USD", statement_unit="USD millions",
        market_cap_currency="USD", market_cap_unit="USD",
        market_cap_label="constructed but wrong scale",
    )
except ValueError:
    pass
else:
    raise AssertionError("unit mismatch should fail")
```

### Challenge Reference Arguments

**12-C01** The supported conclusion is that the listed CFO and PP&E restatements offset under this FCF definition. Net loss also changes from −63,956 to −77,558 USD thousands, demonstrating that profit and cash classification differ. Do not conclude that cash flow was unrevised, or that unchanged FCF implies unchanged enterprise value, shareholder returns, or all cash flows. Check (1) the 10-K/A explanatory note and restatement background; (2) original/restated consolidated income statements, balance sheets, and cash flow statements; (3) PP&E, customer contracts, and embedded-lease accounting notes; (4) period allocation of revenue recognition and contract assets/liabilities; (5) PP&E purchases/capitalization, depreciation, and noncash adjustments; and (6) 8-K non-reliance periods and first revision announcement. An acceptable answer preserves versions, units, cash-flow signs, and the possibility of simultaneous restatement across multiple lines and notes.

Scoring: distinguish checked figures from causal explanations, 2 points; recalculate both FCF versions, 2; propose at least four relevant evidence checks, 3; explain timing/version and extrapolation limits, 2; state what new evidence could change the interpretation, 1.

**12-C02** A minimal auditable model needs at least six logical tables: issuer/security mapping, raw statement facts, document versions, public/submission-time events, vendor ingestion logs, and factor runs. Facts preserve CIK/issuer ID, permanent security ID, original/standardized tags, original line name, value, currency, XBRL unit, duration/instant, fiscal start/end, quarter/year, segment/dimension, accession, version status, and source location. Version events store first_public_at and precision/time zone, filed_date, acceptance_raw, revision_public_at and accession, ingested_at, vendor/batch, and content hash. Mapping stores security class, validity start/end, listing status, and source. Derivation stores signal_time, selected accession, rule/code version, raw-line keys, currency conversion, market-denominator source, executable time, and output units.

Date-only or unverified-zone fields remain date-level; do not invent midnight UTC. Use a conservative later signal date and separately verify trading calendars and data-supply terms. Two counterevidence tests are: (1) removing a later restatement must leave earlier factors unchanged, or the filter leaks; (2) moving ingested_at after signal_time must return the last then-available version or null, or the two-clock implementation is wrong. Additional tests can cover period/currency/unit mismatches, conflicting simultaneous versions, delisted securities, and multiple share classes.

Scoring: traceable raw and derived data, 3 points; correct two-clock and revision-chain preservation, 3; versioned/timed security identity and market value, 2; at least two executable counterevidence tests, 2.

## 19. Further Reading

- **Must Know — SEC investor materials and company filings:** trace a transaction through all three statements; compare Apple FY2024 and Spire FY2023 original/restated filings, recording accession, period, unit, version, and notes. Investor guides do not replace accounting standards.
- **Should Know — SEC EDGAR API and Non-GAAP C&DI 102.07:** understand companyfacts/frames versus company fiscal periods, checking aggregation and common FCF-definition boundaries.
- **Advanced — IAS 7 and IAS 1:** compare cash-flow classification, FX adjustments, and parent/NCI attribution. The cited public HTML editions are 2026 and 2024, respectively; this is not a review of the full standards.

## 20. References

This chapter does not modify shared sources.json or references.bib. The direct links below identify official originals. Reading scope, verification date, raw figures, and timing limits are recorded in [source_notes.md](../../../../part02/chapter12/source_notes.md).

1. SEC, [How to Read a 10-K](https://www.sec.gov/files/reada10k.pdf) and [Beginners’ Guide to Financial Statements](https://www.sec.gov/reportspubs/investor-publications/investorpubsbegfinstmtguide): statement functions and operating/investing/financing cash-flow classification, Sections 3, 5, and 6.
2. SEC, [EDGAR API Documentation](https://www.sec.gov/edgar/sec-api-documentation): companyfacts/frames and calendar versus fiscal periods, Sections 6.4, 11, and 13.
3. SEC, [Non-GAAP Financial Measures C&DIs, Question 102.07](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures): common FCF definitions and limits, Sections 5, 7, and 12.
4. Apple, [FY2024 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm), [accession headers](https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index-headers.html), [2024-10-31 results release](https://www.apple.com/newsroom/2024/10/apple-reports-fourth-quarter-results/): periods, statement lines, units, and distinct disclosure-time fields, Sections 8, 10, and 11.
5. Spire, [original FY2023 Form 10-K](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/spir-20231231.htm), [original accession headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024027164/0000950170-24-027164-index-headers.html), [2024 Form 8-K](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/spir-20240821.htm), [2024 8-K headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017024101007/0000950170-24-101007-index-headers.html), [amended FY2023 Form 10-K/A](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/spir-20231231.htm), [amended accession headers](https://www.sec.gov/Archives/edgar/data/1816017/000095017025030856/0000950170-25-030856-index-headers.html): original, revision notice, restatement, cash-flow lines, and accessions, Sections 6.4, 8, 10, 11, and 18.
6. IFRS Foundation, [IAS 7, 2026 public HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias7.html) and [IAS 1, 2024 public HTML](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2024/issued/ias1.html): IAS 7.11/7.28 and IAS 1.81A/106(a), within the limited scope in Sections 5, 7, and 19.
