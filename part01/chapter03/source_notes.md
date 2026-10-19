# Chapter 3 Source Notes

核验日期：2026-10-05。所有页面均为官方来源。此文件只记录本章实际读取及使用边界，不修改共享 references/sources.json。章节中拆股、EPS、股息和停牌数字均为明确标记的教学构造，不是下载的市场样本。

## 检索与读取方法

- 按本地 agent-reach 技能执行 agent-reach doctor --json。Doctor 将 web 标为 ok，后端是 Jina Reader；Exa 搜索仅列为 warn，未声称连通。随后经 Agent Reach 网页阅读流程读取具体 URL。
- 调用已连接 Tavily Search 官方域名检索 SEC API 时收到 HTTP 429：请求因 excessive requests 被阻止。没有安装 CLI、认证或重试；搜索摘要未作为证据。
- 经 Jina Reader 直接读取下列确切页面。读取日期均为 2026-10-05。后续页面若变化，须以新日期重新核验。
- 本章没有下载 SEC companyfacts、NYSE 行情、交易日历快照或 Kenneth French 因子数据；没有真实市场样本期、频率、文件或 SHA-256，也没有运行实证回测。
- 2026-10-05 浏览了 French Data Library 官方目录页，可见不同频率组合和 Historical Archives 链接；没有读取特定档案或其变更说明。因此本章只把它列为后续入口，不据此陈述修订规则。
- 本章检索和撰写阶段没有下载或分析 French 行业文件。主编另行下载的课程本地 French 行业缓存属于独立工作；本章未用该缓存支持任何数值或历史修订结论。
- 页面可公开访问不自动授权再分发。SEC API 文档指向 SEC Privacy and Security Policy；使用者需按数据源及用途另核许可。

## 本章引用源

### SEC_API

- 页面：[EDGAR Application Programming Interfaces (APIs)](https://www.sec.gov/edgar/sec-api-documentation)
- 读取范围：页面正文，包括 data.sec.gov 总览；submissions；XBRL Company Concepts、Company Facts 和 Frames 端点；Frames 的“最近提交”说明；Bulk Data；Update Schedule；Programmatic API Access。
- 可支持的陈述：SEC 提供 submissions 和 XBRL JSON API；Company Facts 按公司聚合事实；Frames 对指定日历期间取最近提交且匹配最接近的事实；API 会随申报披露更新；批量 ZIP 约每日重发；接口免 API key，但访问须遵守政策。
- 不能支持的陈述：单靠当前 companyfacts JSON 即可恢复任意历史 vintage；某个行情或财报供应商的可用延迟；本地系统实际接收时点；本章已下载或比较过某家公司的事实。
- 下载/快照：未下载数据，无样本期、频率或哈希。

### NYSE_CAL

- 页面：[NYSE Holidays & Trading Hours](https://www.nyse.com/markets/hours-calendars)
- 读取范围：2026、2027、2028 假期表；NYSE 核心交易时段；节后或假日前部分提前收市说明；所有时间为 Eastern Time 的页面说明。
- 可支持的陈述：NYSE 交易时间绑定 Eastern Time；日历包括节假日及特殊提前收市；交易日不能简化为普通周一至周五。
- 不能支持的陈述：本章获得了任何历史行情；所有市场、板块、证券都使用同一交易时段；页面列出的未来日历等同已发布的历史逐笔日历文件。
- 下载/快照：未下载数据，无样本期、频率或哈希。

### PY_ZONEINFO

- 页面：[zoneinfo — IANA time zone support](https://docs.python.org/3/library/zoneinfo.html)
- 读取范围：模块概览；IANA 时区数据库的数据来源；daylight-saving 转换；ambiguous time 的 fold=0/fold=1 语义；America/New_York 等 key 的说明。
- 可支持的陈述：Python zoneinfo 使用系统时区数据库或 tzdata；IANA 时区键表达地点规则；回拨产生的歧义时间需区别处理。
- 不能支持的陈述：某台运行机器必定安装特定版本 tzdata；本章所有环境均实际执行了 DST 验证。

### PANDAS_ASOF

- 页面：[pandas.merge_asof](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html)
- 读取范围：API 定义、升序排序要求、backward/forward/nearest 选择、by 分组、tolerance、allow_exact_matches 和示例。
- 可支持的陈述：merge_asof 用最近键距离连接；backward 选择不晚于左侧时间的最后行；输入要按连接时间升序排列；分组与容差可控制匹配范围。
- 不能支持的陈述：该 API 单独实现了财报双时间版本管理；仅连接 available_at 自动处理 ingested_at；本章已运行此 API。
- 页面当日显示 pandas 3.0.6 文档；本章不据此宣称课程环境或协作代码已固定到该版本。

### FRENCH_LIBRARY

- 页面：[Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library.html)
- 读取范围：官方目录页中的组合数据条目、日/周/月频链接和 Historical Archives 入口。没有打开特定档案或其变更说明。
- 可支持的陈述：目录页提供多个频率和历史档案入口，后续下载需要选择具体数据产品。
- 不能支持的陈述：French 数据发生了某项具体历史修订、某个文件的修订幅度或本章使用过该数据库。
- 下载/快照：未下载数据，无样本期、频率或哈希。


BIL02：沿用上述核读层级，未新增联网读取或市场样本。版本、权限、时钟与公司行动原讲解保留；接受I3读者入口适配见本批SOURCE_MAP。
