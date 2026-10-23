# Chapter prerequisite graph
Solid arrows indicate required preparation; dashed arrows show useful background. Use the chapter numbers to plan your reading, then follow the project milestones in the learning route.
```mermaid
flowchart TD
  C1["Chapter 1 — Quantitative Finance and the Quant Industry"]
  C2["Chapter 2 — Python for Quantitative Research: Getting Returns and Time Indices Right"]
  C3["Chapter 3 — Financial Data Engineering"]
  C4["Chapter 4: Calculus, Rates of Change, Curvature and Local Decisions"]
  C5["Chapter 5: Linear Algebra, Portfolio Objects and Risk"]
  C6["Chapter 6 — Probability"]
  C7["Chapter 7 — Statistical Inference: uncertainty in research conclusions"]
  C8["Chapter 8 — Regression"]
  C9["Chapter 9 — Optimization"]
  C10["Chapter 10 — Financial Markets"]
  C11["Chapter 11 — Returns and Compounding"]
  C12["Chapter 12 — Financial Statements for Quantitative Research"]
  C13["Chapter 13 — Valuation for Quants"]
  C14["Chapter 14 — CAPM and Asset Pricing"]
  C15["Chapter 15 — Factor Models"]
  C16["Chapter 16 — Time Series I: Dependence and ARIMA"]
  C17["Chapter 17 — Time Series II: Unit Roots, Cointegration, and Prediction"]
  C18["Chapter 18 — Volatility Modeling and Forecasting"]
  C19["Chapter 19 — State-Space Models and the Kalman Filter"]
  C20["Chapter 20 — Modern Portfolio Theory"]
  C21["Chapter 21 — Practical Portfolio Construction"]
  C22["Chapter 22 — Quantitative Research Methodology"]
  C23["Chapter 23 — Cross-Sectional Research"]
  C24["Chapter 24 — Value Factors"]
  C25["Chapter 25 — Momentum"]
  C26["Chapter 26 — Quality"]
  C27["Chapter 27 — Carry, Defensive Investing, and Low Volatility"]
  C28["Chapter 28 — Multi-Factor Models: Preprocessing, Combination, and Constraints"]
  C29["Chapter 29 — Building a Backtesting Engine"]
  C30["Chapter 30 — Backtesting Biases"]
  C31["Chapter 31 — Financial Model Validation"]
  C32["Chapter 32 — Performance Statistics & Inference"]
  C33["Chapter 33 — Risk Management"]
  C34["Chapter 34 — Market Microstructure"]
  C35["Chapter 35 — Transaction Costs"]
  C36["Chapter 36 — Algorithmic Execution and Trade Scheduling"]
  C37["Chapter 37. A Foundational Stance on Machine Learning for Finance"]
  C38["Chapter 38: Financial ML Pipeline"]
  C39["Chapter 39 Regularized Linear Models"]
  C40["Chapter 40: Tree-Based Models"]
  C41["Chapter 41: Unsupervised Learning"]
  C42["Chapter 42: Deep Learning Foundations and Quantitative Applications"]
  C43["Chapter 43: Bayesian Inference, Causal Identification, and Alternative Text Data"]
  C44["Chapter 44 — Stochastic Calculus and Derivatives"]
  C45["Chapter 45 — Production Quant Pipelines"]
  C1 --> C2
  C2 --> C3
  C2 --> C4
  C2 --> C5
  C4 --> C6
  C5 --> C6
  C6 --> C7
  C5 --> C8
  C7 --> C8
  C4 --> C9
  C5 --> C9
  C8 --> C9
  C1 --> C10
  C2 --> C11
  C6 --> C11
  C10 --> C11
  C3 --> C12
  C10 --> C12
  C4 --> C13
  C11 --> C13
  C12 --> C13
  C8 --> C14
  C10 --> C14
  C11 --> C14
  C12 --> C15
  C14 --> C15
  C7 --> C16
  C8 --> C16
  C11 --> C16
  C16 --> C17
  C6 --> C18
  C16 --> C18
  C5 --> C19
  C6 --> C19
  C8 --> C19
  C16 --> C19
  C9 --> C20
  C11 --> C20
  C14 --> C20
  C15 --> C20
  C18 --> C21
  C20 --> C21
  C3 --> C22
  C7 --> C22
  C11 --> C22
  C15 --> C22
  C21 --> C22
  C8 --> C23
  C15 --> C23
  C22 --> C23
  C12 --> C24
  C13 --> C24
  C23 --> C24
  C11 --> C25
  C23 --> C25
  C12 --> C26
  C23 --> C26
  C10 --> C27
  C18 --> C27
  C23 --> C27
  C24 --> C28
  C25 --> C28
  C26 --> C28
  C27 --> C28
  C3 --> C29
  C11 --> C29
  C21 --> C29
  C22 --> C29
  C29 --> C30
  C7 --> C31
  C16 --> C31
  C29 --> C31
  C30 --> C31
  C7 --> C32
  C11 --> C32
  C31 --> C32
  C15 --> C33
  C18 --> C33
  C21 --> C33
  C32 --> C33
  C10 --> C34
  C29 --> C34
  C29 --> C35
  C34 --> C35
  C9 --> C36
  C34 --> C36
  C35 --> C36
  C7 --> C37
  C22 --> C37
  C31 --> C37
  C35 --> C37
  C23 --> C38
  C31 --> C38
  C37 --> C38
  C8 --> C39
  C38 --> C39
  C38 --> C40
  C39 --> C40
  C5 --> C41
  C16 --> C41
  C38 --> C41
  C4 --> C42
  C38 --> C42
  C40 --> C42
  C7 --> C43
  C12 --> C43
  C22 --> C43
  C38 --> C43
  C4 --> C44
  C6 --> C44
  C9 --> C44
  C10 --> C44
  C11 --> C44
  C3 --> C45
  C29 --> C45
  C33 --> C45
  C35 --> C45
  C38 --> C45
  C13 --> C15
  C24 --> C26
  C11 -. background .-> C12
  C17 -. background .-> C18
  C33 -. background .-> C34
```

## Reading the prerequisites

- Read Chapter 13 before Chapter 15 for valuation and financial claims, and Chapter 24 before Chapter 26 for accounting conventions and value/quality comparisons.
- Chapters 11, 17 and 33 provide background for Chapters 12, 18 and 34 respectively. Chapter 18 builds on the dependence concepts in Chapter 16; cointegration and VAR are not required for its EWMA/ARCH/GARCH derivations.
- See the [learning route](learning_roadmap.md) for project prerequisites.
