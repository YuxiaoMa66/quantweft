# Capstone研究报告模板

\color{qink}


状态：限定研究设计/技术协议已接受，目标市场执行blocked；当前状态见[Capstone入口](../README.md)。原工程附录保留历史身份，不解释为French市场结果。原通用提示供对照，当前所选French协议不包含模型训练、中性化、笛卡尔网格或DSR/PBO强制计算；逐节以当前设计与导读输出为准。

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


当前已确定：R/P、S01/S02/S06：可报告的现状=问题/协议技术已接受、执行blocked；未来正/零/负/区间跨0有各自解释，工程PASS不回答$\mu_d>0$。详见[第18项导读](REPORT_GUIDE.md#item-18)；目标市场输出：**未执行**。

回答初始假设，区分证据、推测和待验证；成本后无意义也应如实结论。


---

## 工程基础证据附录（A9-B Engineering Base Interface）

\color{qink}


以下保留原A9-B工程附录的历史状态和数字；这些pending/候选词不覆盖当前A10-A/A10-A.1接受设计，也不表示市场研究已经执行。当前口径见[研究入口](../README.md)与上面18项导读。

状态：A9-B 工程基础建设阶段已完成，提供离线生产管线、质量闸门、持久化账本与对账闭环；所有真实研究与策略开发工作显式标注为 `pending_A10`。

### 18 章节工程证据与研究状态映射表

\color{qink}


| 报告章节 | 当前状态 | 工程基础证据 / 交付物索引 | 说明 |
|---|---|---|---|
| 1. Research Hypothesis | `pending_A10` | 暂无策略假设，仅验证框架接口 | 待 A10 确定正式研究假说 |
| 2. Data Sources | `pending_A10` | `CONSTRUCTED_TEACHING_DATA` v1.0.0 | 无外部真实数据下载 |
| 3. Data Dictionary | `pending_A10` | `capstone/data_dictionary.md` 附录 | 仅提供构造字段工程字典 |
| 4. Point-in-Time Logic | **`author_candidate_pending_independent_acceptance`** | 满足 $\max(\text{avail}, \text{ingest}, \text{as\_of}) \le \text{signal} < \text{trade}$ | 构造时点契约和拒绝测试，待独立接受 |
| 5. Data Cleaning | **`author_candidate_pending_independent_acceptance`** | 陈旧阈值($\le 3600\text{s}$)、严格正价、非空非重复检验 | 成交前拒绝本批契约中列明的异常 |
| 6. Feature Engineering | `pending_A10` | 单期教学动量 $(P_t - P_{t-1})/P_{t-1} > 0$ | 待 A10 正式特征工程与消融 |
| 7. Signal Construction | `pending_A10` | 教学固定分配股数 (A:10, B:20) | 待 A10 截面排序与中性化 |
| 8. Portfolio Construction | `pending_A10` | 教学固定仓位，事前杠杆率核查 $0.20 \le 0.50$ | 待 A10 预登记正式组合方法 |
| 9. Transaction Cost Model | **`author_candidate_pending_independent_acceptance`** | 点差 10bps 内嵌于成交价，佣金 10bps 显式计提 | 零重复扣费，总成本 4.002 USD |
| 10. Walk-Forward Validation | `pending_A10` | 暂未执行滑动窗口切分 | 待 A10 真实滚动样本外回测 |
| 11. Performance Analysis | `pending_A10` | 基线期末净值 9995.998 USD，净亏损 -4.002 USD | 教学算例非真实策略阿尔法 |
| 12. Risk Analysis | **`author_candidate_pending_independent_acceptance`** | -10% 市场冲击情景损失 200.0 USD $\le$ 1000.0 USD 限额 | 压力测试与事前杠杆门禁通过 |
| 13. Factor Attribution | `pending_A10` | 暂无多因子分解 | 待 A10 按项目2单位/RF/HAC规则选择归因 |
| 14. Robustness Tests | `pending_A10` | 暂无参数鲁棒性扰动 | 待 A10 子样本与敏感性分析 |
| 15. Parameter Sensitivity | `pending_A10` | 暂无参数网格扫描 | 待 A10 参数响应面分析 |
| 16. Overfitting Discussion | `pending_A10` | 暂无多重测试检验 | 待 A10 计算 PSR/DSR/PBO |
| 17. Limitations | **`author_candidate_pending_independent_acceptance`** | 离线单进程环境，构造教学数据，无实盘市场冲击 | 明确工程边界，无外推推论 |
| 18. Final Research Conclusion | `pending_A10` | 构造工程接口候选，策略有效性检验留待 A10 | 不作任何未经实证的投资结论 |

\color{qink}


## R2工程修订

\color{qink}

R01–R04反例/STOPPED/覆盖与实际次序证据见 `qa/a9/ch45_batch/revisions/r2_20261012`；金额容差1e−6 USD、真实数股数支持域和三类恢复路径见ENGINEERING_BASE。所有真实研究栏目仍pending_A10；本附录不填真实成果、不登记接受。
