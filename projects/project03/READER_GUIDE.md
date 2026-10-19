# Project 3 独立运行导读

项目把第21章的稳定估计、长仓约束、风险预算和漂移费用连成一个滚动评价流程。先完成默认离线构造演示，再用完整历史报告练习统计判断；两者输入、窗口和证据身份不同。

## 默认入口与输入

在随书读者包根目录，按包内环境说明建立独立环境后运行：

```bash
.venv/bin/python run_notebook.py projects/project03/notebooks/project03_portfolio_oos.ipynb
```

Notebook默认只执行构造分支，不执行French分支。种子103生成2000-01起48个月的四资产A/B/C/D独立正态月度简单收益，均值0.005、标准差0.03；RF恒为0.001。前24个月提供首个训练窗，2002-01至2003-12共24个月持有。`Spec(window=24,max_weight=0.4)` 其余默认是Ledoit–Wolf与滞后0。等权各0.25；最小方差与最大Sharpe受0.4上限约束，ERC无上限。

每月只用此前24个月估计，再持有一个月。首月从现金建仓，权重换手代理为1；后续用漂移权重计算买卖合计换手，不除以2。成本率10bp，净收益按 `(1-cost)*(1+gross)-1` 计算；这是费用代理，不是精确自融资成交额账本。核对训练末月早于持有月、四策略各24行，完成时96行。

## 应看到的输出

项目 `RUN_DIR` 为 `runs/project03_portfolio_oos_<uuid>/`，其中只写六个文件：

- `constructed_primary_metrics.csv`；
- `equal_weight_ledger_CONSTRUCTED.csv`；
- `min_variance_ledger_CONSTRUCTED.csv`；
- `max_sharpe_ledger_CONSTRUCTED.csv`；
- `erc_ledger_CONSTRUCTED.csv`；
- `project03_wealth_CONSTRUCTED.png`。

运行器另建 `runs/execution_project03_portfolio_oos_<uuid>/` 保存执行副本和状态，不能与项目运行目录混同。构造财富图含初始1，共25个点；原Holding month横轴是0至24的位置序号，0为首个持有月前，不是日历日期。默认不下载或读取French，不运行历史主规格、参数网格、Bootstrap或后见之明分析，也不生成它们的summary.json等文件。保存的旧输出若存在，仅是原文件携带的记录，不是本轮执行证据。

## 如何阅读完整历史材料

[README](README.md)说明研究目标与完整研究契约；[字典](data_dictionary.md)列历史字段并解释默认差异；[六道练习](exercises.md)与[完整答案](solutions.md)保留全部推导、代码及历史结果；[报告](research_report/report.md)完整呈现四策略、440个月/1760行、主规格W60、10bp、LW、滞后0及所有负零结果。

P3-02需要历史primary_ledger.csv，P3-05需历史French数据和工作根代码，不在默认构造输出内。缺少这些输入时使用给出的完整历史参考解，不要求运行市场分支。默认构造W24也不是历史事后W24（净Sharpe约0.587、25次回退）的再现。

历史报告的5000次、12个月成对循环块Bootstrap和三策略×两指标的未校正区间，只支撑给定重抽样方案的判断；跨零不证明等价，筛选失败不等于正式联合检验拒绝。French是当前修订快照、非PIT；行业发布组合不可直接交易。数据权利与研究闸门沿用原规定，公开可下载不构成新的使用或再分发授权。

## 两种语言的Notebook

中文与英文项目Notebook由同一个已接受读者源投影，仅Markdown语言与默认运行说明不同；代码单元格、保存输出及metadata保持原样。本轮不重新执行Notebook。最终读者包的路径装配与运行验证仍须在整合时完成；本导读不把语言层校验称为一次新的数值或市场验证。
