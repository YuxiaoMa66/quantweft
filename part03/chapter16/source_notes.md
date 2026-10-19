# 第 16 章来源核验与边界

核验日期：2026-10-06。网页发现走 agent-reach 的 Exa 搜索，页面正文走 Jina Reader。教材公式由本章按所列假设独立推导；来源用于核对定义范围、模型/API 参数和数据身份，不把搜索标题当正文证据。

## 官方技术文档

本地 `quant_course/.venv` 实测 Python 3.14.7、statsmodels 0.15.0；本次读取的 stable 文档也标示 0.15.0。

- [statsmodels `ARIMA`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html)：核对 `(p,d,q)`、趋势项、缺失处理、`enforce_stationarity` 与 `enforce_invertibility`。文档说明趋势项作为回归项进入 ARIMA-errors 规格，故正文专门区别 statsmodels 的 `const` 与递推式 `X_t=c+\phi X_{t-1}+\varepsilon_t` 中的 `c`；本地拟合模拟序列也得到 `const` 接近样本均值。
- [statsmodels `ARIMAResults.get_forecast`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMAResults.get_forecast.html)：核对 `steps` 是从样本末尾向外预测的步数，以及返回对象包含样本外预测和区间。
- [statsmodels `acf`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html)：核对 `adjusted=False` 使用分母 `n`、返回值包含滞后 0，以及 `missing="raise"` 的行为；本章验证器先拒绝缺月和缺失，再计算 ACF。
- [statsmodels `pacf`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.pacf.html)：核对 `ywadjusted` 是支持的 PACF 估计方法；正文把 PACF 作为候选辨认线索，不宣称不同估计器有限样本相同。
- [statsmodels `acorr_ljungbox`](https://www.statsmodels.org/stable/generated/statsmodels.stats.diagnostic.acorr_ljungbox.html)：核对 `model_df` 从滞后自由度中扣除，ARMA 常取 `p+q`，p 值使用相应卡方参考分布，且返回统计量和 p 值。章节内的 Ljung–Box 统计量按常用定义写出；大 p 值只解释为未拒绝联合零自相关原假设。
- [statsmodels `ArmaProcess`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima_process.ArmaProcess.html)：核对 AR 和 MA 滞后多项式的系数符号约定，以及 AR 根在单位圆外对应平稳、MA 根在单位圆外对应可逆。章节明确提醒不同教材的 MA 符号惯例可能不同。

以上 API 页面已通过 Jina Reader 读取相关参数说明。它们支持实现和软件接口的陈述，不证明任何金融序列满足模型假设或具有预测能力。

## 大学课程讲义

- MIT OpenCourseWare，[18.S096 Topics in Mathematics with Applications in Finance，Lecture 8: Time Series Analysis 1](https://ocw.mit.edu/courses/18-s096-topics-in-mathematics-with-applications-in-finance-fall-2013/1926c83ecd7ea700f7cb63914c6d7c0f_MIT18_S096F13_lecnote8.pdf)，Fall 2013，共 33 页。Jina Reader 可读取 PDF；本章核对其第 3–5 页严格/协方差平稳与 Wold 表示、第 10 页滞后算子、第 17–20 页 AR(1)、ARMA/MA、第 25 页 ARIMA 的讲授范围。PDF 文本抽取中的部分公式字符有 OCR 错位，因此只用来确认课程覆盖和术语范围，不照录 OCR 公式；正文的 AR(1)、MA(1) 与差分等式均独立推导。

## 原始论文及可访问范围

- Ljung, G. M., & Box, G. E. P. (1978). “On a measure of lack of fit in time series models.” *Biometrika*, 65(2), 297–303. DOI: [10.1093/biomet/65.2.297](https://doi.org/10.1093/biomet/65.2.297)。Oxford Academic 的期刊条目检索结果核对了题名、作者、卷期、页码和 DOI；本次 Jina Reader 被安全验证页拦截，网页阅读器 MCP 未配置，Web 打开器也无法读取其转发内容；Penn 讲义镜像请求超时。因此，本章没有声称阅读全文，也不把无法直接读取的论文内容当作公式依据。论文在此用于标记 Ljung–Box 检验的原始出处；检验统计量、自由度与 API 行为以已读取的 statsmodels 文档核对。

## French 行业收益数据

- [Kenneth R. French Data Library：10 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_10_ind_port.html)。数据身份和转换记录按本地清单 [`french_industries_2026-10-05.json`](../../data/manifests/french_industries_2026-10-05.json) 核对：原始 ZIP 下载于 2026-10-05，SHA-256 `ebd937a4b995d821867aeb956a96f09a666386f38fa82516b7d1767ee4a49ae5`；选取 `Average Value Weighted Returns -- Monthly` 区块，将源百分数除以 100，处理后 CSV SHA-256 `3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950`。缓存有 1,202 个月，区间 1926-07 至 2026-08；本章取 NoDur 月简单收益作描述统计。
- 该文件是当前发布快照，不含逐月历史版本、历史公开时间或数据入库时间；因此不能据此声称 PIT 预测、策略表现、因果关系或可交易净收益。公开下载也不等同于任意再分发许可。



## 2026-10-15 BIL09作者候选

保留已接受C8全部推导、35道正文题与17道Loom题的对应原题和完整答案。实际逐格静态读取I3两章Notebook及共享消费者；新增默认离线路线说明，区分历史French制作路径、随包既有图与执行目录。第16章澄清固定因果差分本身不必然泄漏。第16章Notebook第0、6格仍有读取French的旧描述；默认第7格实际跳过NoDur历史统计。 第17章另将普通ADF对象校正为事先规定的序列/组合（不预设平稳），并将图17-2横轴明确为收益所属月份而非发布时间；两语一致，数值与代码不变。本批未重跑旧数值、Notebook、French或CLI，未重访外部来源；历史文献核验范围沿用。Project5仅只读接口，真实实证仍blocked；未改研究闸门。三张原PNG已实看，标题/轴/图例均为英文，直接共用且字节不变。Notebook英文Markdown及旧叙述校正留BIL23实际装配。待根独立接受；canonical_written=false、formal_publication=false、final_verified=false。
