# Project 3 — Portfolio Optimization

本项目包含默认离线构造演示与完整历史研究读物。先读[独立运行导读](READER_GUIDE.md)，再读[数据字典](data_dictionary.md)、[六道练习](exercises.md)、[完整答案](solutions.md)及[历史研究报告](research_report/report.md)。默认演示不复现French历史报告。

## 研究目标与数据

先修章节：9, 18, 20, 21。

同币种资产或可验证行业/ETF总回报数据；供应商可用性、历史覆盖和存活者限制另行核验。

## 工作步骤

1. 实现Equal Weight、Minimum Variance、Maximum Sharpe、Risk Parity/ERC。
2. 每个再平衡时点仅用过去窗口估计收益与协方差。
3. 加入权重上限、现金、交易成本与可行性检查。
4. 对比样本外净表现、换手、集中度与参数敏感性。

## 时间与评价规则

所有输入必须说明event_time、available_at、signal_time、trade_time、return interval及label interval（如适用）。收盘信号在下一可交易时点执行。训练内确定模型与参数，测试只作评价；成本、融资和借券口径列配置。

## 交付文件

- data_manifest.json：下载来源、许可边界、样本、单位、SHA-256及数据版本。
- data_dictionary.md：字段、单位、主键、时间与缺失规则。
- notebooks/：从干净kernel执行；核心逻辑复用src/。
- src/、tests/、configs/：可运行脚本、核心测试与冻结配置。
- figures/：图轴说明、数据与代码版本。
- research_report/：假设、方法、训练/测试、指标、风险、成本、稳健性、限制和结论。
- solutions.md：六道练习的完整参考解、题号与历史结果核对。

## 实现检查

最大Sharpe不能无证明地写成凸QP；ERC给风险贡献核对；协方差PSD、求解状态和预算约束通过。

报告不可用数据造成的局限，保留所有零与负结果。核心逻辑经pytest、脚本和Notebook冷启动验证；实测结果不得由教学模拟替代。

## 历史研究交付（2026-10-06）

以上列出完整研究任务的文件与检查要求；本节描述历史研究，不能当作默认离线演示的运行产物。

- 数据：French 10 行业价值加权月收益与 FF3 RF，2026-10-05 冻结快照（当前修订历史，非 PIT，行业组合不可直接交易）。[data_manifest.json](data_manifest.json)、[data_dictionary.md](data_dictionary.md)。
- 冻结配置：[configs/project03.json](configs/project03.json)。主规格 W=60、Ledoit–Wolf、10 bp/单位换手、最小方差/最大Sharpe上限 40%（ERC无上限）、滞后 0；评价 1990-01..2026-08（440 个月）；敏感性 W∈{36,60,120} × {sample, LW} × 滞后{0,1} × 成本{0,10,25,50} bp。
- 代码：[src/project03_backtest.py](src/project03_backtest.py)（账本、回退、指标、块自助法）复用 src/quant_course/portfolio_construction.py、optimization_tools.py、performance.py、statistics_tools.py；入口 run_project03.py；测试 tests/test_project03_backtest.py。
- 时点：持有月 t 的权重在 t−1 月末用 [t−W, t−1]（滞后 1 时 [t−W−1, t−2]）估计并成交；漂移后的交易前权重计算换手；净收益 = (1−成本)(1+毛收益)−1。
- 结果：[研究报告](research_report/report.md)。三种估计矩的组合在成本后都没有可信地优于等权；最小方差相对等权的年化平均净收益差的未校正单项区间低于零（年化约 −2.0%，块自助法 95% 区间不含 0），波动与回撤更低；最大 Sharpe 换手最高、对成本和窗口最敏感；ERC 与等权 Sharpe 差区间跨 0。所有负结果与零结果保留。
- 图：figures/projects/project03_net_wealth.png、project03_weights.png、project03_cost_window_sensitivity.png、project03_bootstrap_difference.png。
- Notebook：[notebooks/project03_portfolio_oos.ipynb](notebooks/project03_portfolio_oos.ipynb)。练习与解答：[exercises.md](exercises.md)、[solutions.md](solutions.md)。

以下是历史课程工作根路线，需要另有合适且获授权的数据与环境，不是读者包默认命令：

```bash
.venv/bin/python projects/project03/run_project03.py
.venv/bin/python -m pytest tests/test_project03_backtest.py -q
```

口径说明：账本含信息截止、成交区间及漂移后的交易前权重；成本为归一化权重换手代理，精确自融资金额方程和误差边界见报告§3。年化平均费用与实际毛净收益差分开报告；统计结论只称未通过优势筛选，不将未显著误写为证明无效。
