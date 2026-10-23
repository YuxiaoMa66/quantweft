# Capstone研究报告模板

\color{qink}


该模板区分构造工程示例与French市场研究。时间与权利限制见[Capstone入口](../README.md)。当前French协议不包含模型训练、中性化、笛卡尔网格或强制DSR/PBO计算；逐节以当前设计与导读为准。

## 1. Research Hypothesis

\color{qink}


当前已确定：S01/S02：固定French十行业、L11/skip1/top3、EW10；H0 $\mu_d\le0$/$H_1:\mu_d>0$；一月是实验单位，缓慢反应不是已识别因果。详见[第1项导读](REPORT_GUIDE.md#item-1)；目标市场输出：**未执行**。

先验经济机制、目标资产/频率、可证伪预期、基准及登记时间。

## 2. Data Sources

\color{qink}


当前已确定：S08/S09、R/P：2026-10-05修订快照、industry/FF3身份与下载UTC；G01主体/用途unknown，原始再分发未计划=not_requested。详见[第2项导读](REPORT_GUIDE.md#item-2)；目标市场输出：**未执行**。

来源URL、许可、下载UTC时间、覆盖范围、哈希与供应商修订；缺口不补造。

## 3. Data Dictionary

\color{qink}


当前已确定：S04/S03：长表(snapshot_id,month,industry_id)，十行业小数总收益，FF3/RF，score/weight/金额/net return/标签成熟字段。详见[第3项导读](REPORT_GUIDE.md#item-3)；目标市场输出：**未执行**。

字段、主键、类型、单位、频率、时间字段、缺失和修订规则。

## 4. Point-in-Time Logic

\color{qink}


当前已确定：S03：半开[B_t,B_(t+1))；S=B_t−1秒、allocation=B_t只是假设顺序；available/ingested/revision仍unknown；正常/未来两行是CONSTRUCTED。详见[第4项导读](REPORT_GUIDE.md#item-4)；目标市场输出：**未执行**。

公告/可用/入库/信号/成交/收益/标签时间表；as-of join与反例测试。

## 5. Data Cleaning

\color{qink}


当前已确定：S02/S04/S06：重复month/行业、缺月、非有限/缺失拒绝；原百分数只除100一次；总收益公司行动不重复加现金。详见[第5项导读](REPORT_GUIDE.md#item-5)；目标市场输出：**未执行**。

去重、缺失、错误价、拆股/分红/退市；清洗前后计数与可追溯日志。

## 6. Feature Engineering

\color{qink}


当前已确定：S02/S03/S05：$\mathrm{score}_{i,t}=\prod_{m=t-12}^{t-2}(1+R_{i,m})-1$，11项；一般[t−skip−L,t−skip−1]；首评价月各窗口已列。详见[第6项导读](REPORT_GUIDE.md#item-6)；目标市场输出：**未执行**。

数学定义、单位、窗口端点、train-only拟合、经济意义和数据消融。

## 7. Signal Construction

\color{qink}


当前已确定：S02/S05：固定10行业顺序，score降序/manifest索引升序破平，主top3每项1/3，敏感性每项1/k；无拟合。详见[第7项导读](REPORT_GUIDE.md#item-7)；目标市场输出：**未执行**。

排序、缩尾、中性化、缺失处理与合成权重；方向和时间核验。

## 8. Portfolio Construction

\color{qink}


当前已确定：S02：$V_{post}=V_{pre}-c\sum_i|w_iV_{post}-x_i|$；x为漂移金额；长仓全额gross=net=1；首月1/(1+c)，段边界不重置。详见[第8项导读](REPORT_GUIDE.md#item-8)；目标市场输出：**未执行**。

预算、gross/net、sector/beta、leverage、现金、漂移、可行性与再平衡。

## 9. Transaction Cost Model

\color{qink}


当前已确定：S02/S05/S06：all-in费用=c×绝对成交金额，其中c=.001，不除2、不再扣点差；200.10×.001=.20010；$(1-.001)(1+.02)-1=.01898$为不同构造金额例。详见[第9项导读](REPORT_GUIDE.md#item-9)；目标市场输出：**未执行**。

佣金、价差、冲击、融资、借券、容量及校准边界；gross到net的对账。

## 10. Walk-Forward Validation

\color{qink}


当前已确定：S02/S03/S05/S07：18预热，440=176/132/132，唯一主段2015-09..2026-08；13路径连续，边界承接，不假造训练；已曝光非盲holdout。详见[第10项导读](REPORT_GUIDE.md#item-10)；目标市场输出：**未执行**。

训练/选择/最终测试、滚动日历、overlap/purge/gap、拟合/预测的可用时点。

## 11. Performance Analysis

\color{qink}


当前已确定：S02/S05：d=M0net−EW10net；主n132、k1、共同n分母gamma、Bartlett6、$q=132/131$作用协方差、$\operatorname{SE}=\sqrt{\widehat\Omega/131}$、近似t131；bootstrap12/5000/seed固定。详见[第11项导读](REPORT_GUIDE.md#item-11)；目标市场输出：**未执行**。

CAGR/Sharpe/Drawdown等、依赖下区间、简单基准与分期；不只报最佳期。

## 12. Risk Analysis

\color{qink}


当前已确定：S01/S02/S06：top3集中、行业权重/最大回撤/历史尾部；统一构造−10%冲击只证风险公式；无量/盘口不估ADV容量。详见[第12项导读](REPORT_GUIDE.md#item-12)；目标市场输出：**未执行**。

因子/行业/集中度/尾部/流动性/杠杆/保证金与压力情景。

## 13. Factor Attribution

\color{qink}


当前已确定：S02/S05：同月净总收益减FF3 RF一次，发布Mkt-RF/SMB/HML不再减RF；含常数k4修正$n/(n-4)$；主配对d不扣RF、k1。详见[第13项导读](REPORT_GUIDE.md#item-13)；目标市场输出：**未执行**。

同频同币种RF、CAPM/FF、HAC选择、残差与alpha解释范围。

## 14. Robustness Tests

\color{qink}


当前已确定：S02/S05/S06：成本/skip/固定分期及统计block6/24敏感性全报告，负/零也保留，不用interval选口径。详见[第14项导读](REPORT_GUIDE.md#item-14)；目标市场输出：**未执行**。

预先指定的子样本、替代口径、成本、延迟、极端期、消融和替代基准。

## 15. Parameter Sensitivity

\color{qink}


当前已确定：S02/S05：M0/C0/C25/C50/L5/L17/K2/K4/S2九策略+四EW费用，优化0；单因素不做笛卡尔积。详见[第15项导读](REPORT_GUIDE.md#item-15)；目标市场输出：**未执行**。

参数网格、所有试验、稳定区间与图；不能依测试最优重新登记。

## 16. Overfitting Discussion

\color{qink}


当前已确定：S07/S02：P3已见全1990..2026，P1/P2部分历史，其他访问unknown；not blind/full_preregistration=false；PSR/DSR/PBO适用性不足可N/A。详见[第16项导读](REPORT_GUIDE.md#item-16)；目标市场输出：**未执行**。

研究自由度、多重测试、PSR/DSR/PBO适用条件、搜索遗漏与最终holdout限制。

## 17. Limitations

\color{qink}


当前已确定：R/P、S02/S04/S10：许可未明、历史PIT未知、虚拟配置非真实成交/ETF复制、无容量校准；旧P6/39缺口保留；月收益adapter未实现。详见[第17项导读](REPORT_GUIDE.md#item-17)；目标市场输出：**未执行**。

数据、交易、统计、模型、市场制度、容量和部署差距；明确无法支持的推论。

## 18. Final Research Conclusion

\color{qink}


未来正/零/负/区间跨0有各自解释，工程PASS不回答$\mu_d>0$。

回答初始假设，区分证据、推测和待验证；成本后无意义也应如实结论。


---

## 构造工程示例：覆盖范围与限制

\color{qink}


本附录描述离线构造工程示例覆盖的内容和研究缺口；数值均属于教学构造数据，不是French市场结果。

离线工程示例覆盖数据输入、质量检查、信号、模拟成交、账本、风险、对账与报告；真实研究与策略结论未产生。

### 18项报告主题的实现范围

\color{qink}


| 报告章节 | 实现范围 | 构造工程示例 | 研究缺口 |
|---|---|---|---|
| 1. Research Hypothesis | No strategy hypothesis | Framework interface only | No French-market hypothesis is tested |
| 2. Data Sources | Constructed input | `CONSTRUCTED_TEACHING_DATA` v1.0.0 | No external real-data download |
| 3. Data Dictionary | Constructed fields | `capstone/data_dictionary.md` appendix | Engineering dictionary only |
| 4. Point-in-Time Logic | Constructed time contract | 满足 $\max(	ext{avail}, 	ext{ingest}, 	ext{as\_of}) \le 	ext{signal} < 	ext{trade}$ | 构造时点契约和拒绝测试；French历史事件时间仍未知 |
| 5. Data Cleaning | Constructed checks | 陈旧阈值($\le 3600	ext{s}$)、严格正价、非空非重复检验 | 拒绝成交前契约列明的异常 |
| 6. Feature Engineering | One-period teaching momentum | $(P_t - P_{t-1})/P_{t-1} > 0$ | French月度特征与消融尚未实现 |
| 7. Signal Construction | Fixed teaching quantities | A: 10, B: 20 | 未运行French截面排序或中性化 |
| 8. Portfolio Construction | Fixed teaching positions | 事前杠杆率核查 $0.20 \le 0.50$ | 未运行French组合方法 |
| 9. Transaction Cost Model | Constructed cost example | 点差10bps内嵌于成交价；佣金10bps显式计提 | 零重复扣费，总成本4.002 USD |
| 10. Walk-Forward Validation | Not run | 未执行滑动窗口切分 | 未进行真实滚动样本外回测 |
| 11. Performance Analysis | Constructed result | 基线期末净值9995.998 USD；净亏损−4.002 USD | 教学算例，不是策略alpha |
| 12. Risk Analysis | Constructed scenario | −10%市场冲击情景损失200.0 USD $\le$ 1000.0 USD限额 | 仅为构造情景结果 |
| 13. Factor Attribution | Not implemented | 暂无多因子分解 | French归因未执行 |
| 14. Robustness Tests | Not run | 暂无参数鲁棒性扰动 | 未做子样本或敏感性分析 |
| 15. Parameter Sensitivity | Not run | 暂无参数网格扫描 | 未生成参数响应面 |
| 16. Overfitting Discussion | Not run | 暂无多重测试检验 | 未计算PSR/DSR/PBO |
| 17. Limitations | Scope boundary | 离线单进程、构造教学数据、无实盘市场冲击 | 不外推到真实市场 |
| 18. Final Research Conclusion | No market conclusion | 仅构造工程接口 | 未检验策略有效性 |

\color{qink}


## R2工程修订

\color{qink}

金额容差为1e−6 USD；真实数股数支持域和三类恢复路径见[工程入口](../ENGINEERING_BASE.md)。这些软件行为不提供真实市场结果，也不构成市场验证。
