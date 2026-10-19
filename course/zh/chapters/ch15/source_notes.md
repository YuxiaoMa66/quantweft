# 第15章来源记录（正文与配套已验收）

核验日期2026-10-06。French三因子与五因子官方说明页通过Tavily Extract及网页正文读取：SMB/HML/RMW/CMA的分组收益关系、五因子SMB三组size spreads平均、月RF代理来源、July-to-June财报资格。Tavily相关性提取曾返回较旧月份范围，而本轮网页正文和冻结文件头均显示August/202608；方法陈述与快照年月分开核对，不以缓存片段替代本地文件版本。详见原始manifest与qa/a4准备contract。

- [French三因子方法](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html)
- [French五因子方法](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_5_factors_2x3.html)
- [statsmodels robustcov API](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html)：读取use_t与HAC段，核对maxlags、Bartlett核、use_correction。cluster的df_correction不能误写成普通HAC参数规则。公式的有效性不由软件选项保证。

两份原刊PDF已找到并读取若干部分，不声称已读完整全文：

- [Fama & French 1993，原刊PDF，大学教学镜像](https://www.bauer.uh.edu/rsusmel/phd/Fama-French_JFE93.pdf)：标题/作者/Journal of Financial Economics33，3–56；读取Introduction及§2.1.2相关文字。原文研究同时含三个股票与两个债券风险因子，不能把1993文中五因子称为2015股票五因子。时间序列斜率与截距的研究意义有原文支撑，具体历史表统计未用于本章数据结果。
- [Fama & French 2015，原刊PDF，教学镜像](https://tevgeniou.github.io/EquityRiskFactors/bibliography/FiveFactor.pdf)：原刊22页，JFE116，1–22；读取Introduction与§7若干文字，核对HML冗余陈述带原论文美国1963–2013样本限定。原文上线日2014-10-29不改其期刊2015年份。尚未逐式视觉核验原刊公式，不据OCR直接转录公式或表统计。

此处链接的是论文原文镜像而非二手解读；能读取并不表示获准重新分发原文或图表。教材使用自写解释与原创算例；引用范围限实际读取部分。FF3/FF5快照同名市场差异上游原因尚未确定，不猜测为论文机制或数据修订。尚无逐股复制因子构造/PIT或交易成本后业绩，当前实证是行业组合历史归因。

新增HAC手算核验：四月构造样本、Bartlett L=1，Gamma0/Gamma1/meat/协方差矩阵逐项复算，有限样本因子T/(T−p)与本地0.15.0源码/helper对照；见 教学例核验。不将4个观察的软件推断输出当作可信统计证据。


## 2026-10-15 BIL08 作者候选

完整对照工作正文、notes、plan、Loom、接受I3正文TeX及章Notebook源；保留全部原题与同章完整答案、推导、代码、历史数值及负/零结果。第15章默认构造运行与历史French制作分开，未执行Notebook、旧市场回归或重新访问外部资料。第15章两张横向区间图的轴说明按实际绘图函数校正；章Notebook第4/18格旧历史叙述待BIL23校正。作者候选待根独立验收，canonical_written=false、formal_publication=false、final_verified=false。
