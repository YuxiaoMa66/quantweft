# 可选数据与输入契约

默认路线离线，French原始、提取与处理数据均不随包。G01的实际主体、用途与权利仍unknown；G05未授权A10-B。A10-A设计仅限定接受，A10-A.1为技术协议接受，不是市场执行许可。公开可得不等于研究使用或再分发获准。不要为运行本Notebook下载市场数据或把构造数据冒称缺失历史市场输入。

历史辅助模块期望以下路径，均不是A已分发数据：

```text
data/processed/french_10_industries_monthly.csv
data/manifests/french_industries_2026-10-05.json
data/manifests/french_factors_2026-10-05.json
```

历史行业处理快照SHA-256为3b097d810c295d64eedfa1ece7067ff2a0707f5ca90e33935df9949251f70950；列为month、NoDur、Durbl、Manuf、Enrgy、HiTec、Telcm、Shops、Hlth、Utils、Other。收益已是小数。此身份只对应那份快照，不接受任意文件替换后仍称复现历史数字。

若日后取得实际主体/用途权利与执行授权，应在自己的工作副本核字段、币种、单位、月份连续性、SHA及来源，通过表格/数组接口提供输入；修改原快照专用断言须留记录。不能从月份标签推出公告、入库或成交时点。两语共用一套数据契约，不分别下载两份。

Project 1–3的历史接受绑定原版本与范围，不升级为股票级PIT或可交易结论。Project 4–6真实市场实证仍有原记载的blocked/证据缺口；构造方法通过不能补齐。第39章旧逐行预测与共同日期配对证据仍缺失，不补造或重训。固定摘要与图片是原记录的历史展示，不是本轮重验。所有负、零结果保留，unknown/blocked不写成零效果。

Capstone提供已接受的研究问题、时间契约、完整协议、字典和18项报告导读，以及固定两资产离线构造工程。French月收益配置只作参数教学，市场adapter未实现，目标市场研究与结果尚未产出。工程PASS不回答目标净均值优势。已曝光历史不能恢复为盲holdout，历史available/ingested/revision时钟仍unknown。

[逐本模式与可选分支](NOTEBOOK_GUIDE.md) · [市场状态](MARKET_EMPIRICAL_STATUS.md)
