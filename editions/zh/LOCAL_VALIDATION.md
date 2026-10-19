# 本地验证范围

本地正式版（2026-10-19）。已获用户授权更新本地正式版；canonical_written=true，formal_publication=false。本轮核验范围是本地正式版提升和身份，不扩大历史实验或研究验证范围。

## 四本完整PDF

[中文正文](body/main.pdf)、[中文Loom](loom/main.pdf)与英文对应两本覆盖第1–45章、项目1–6与Capstone的全部教学内容和题答，项目放在其先修章节之后。四本PDF经两路独立验收：内容与渲染审阅（逐项对照源文件、复算新增题答的关键数值）以及整书逐页缩略图审阅；目录、书签、书内跳转与本地文件链接用PDF解析逐项核对，无指向构建目录的链接。语义彩框覆盖完整例题的题干、全部步骤与结论，跨页续框带续接标记。英文正文中的图均为英文标注：原带中文标注的两幅共用图（第10章现金流时间线、项目1仪表图）用同一代码与数据重绘，只翻译标注文字；中文正文仍用原图。

## 隔离冷启动（实际执行）

把本包复制到课程工作目录之外的空目录，按[入口](README.md)原样执行：

- 环境：macOS arm64、CPython 3.14.7，新建`.venv`，`pip install -r requirements-macos-arm64-py314.lock`（仅安装时从公共PyPI联网），安装结果与锁文件75项逐一一致；`ipykernel install --prefix .venv`后确认Notebook内核使用该`.venv`解释器。
- 离线测试：`PYTHONPATH=src .venv/bin/python -m pytest tests -q`，197项通过（含第8、32章修正后的回归与推断测试）。
- Notebook：用`run_notebook.py`以全新内核逐本执行中文54本、英文54本语言视图，108本全部PASS；两语代码单元相同，各次输出写入独立的`runs/execution_*`与`runs/<名称>_*`目录。
- Capstone：`capstone/check_portable.py`通过（故障注入后同任务恢复、重放幂等）；按[工程说明](../../capstone/ENGINEERING_BASE.md)运行`run_offline.py`：带故障运行按预期中止，同一state-db、run key与output-dir恢复后对账PASS、期末NAV 9995.998，重放结果一致；同一key换输出目录被拒绝。
- 运行后核对：除`.venv/`与`runs/`外，包内文件无新增、无修改。

## 未执行与边界

市场数据分支（G01权利未知、G05未授权A10-B）、Docker、未列入运行矩阵的历史命令行、其他平台与Python版本均未执行。构造结果只检验方法与实现，不是市场证据。文档中指向课程工作目录内历史QA与审计记录（`qa/`等）的链接不随包分发；章节正文的读者路线以PDF为准。

[后续事项](REMAINING_ITEMS.md) · [入口](README.md)


## 本次正式版提升

2026-10-19仅更新版本说明与正式入口。四本PDF及共用代码、依赖、配置、题答和Notebook均沿已接受B4/C3字节。C3新核check_portable、故障恢复/重放/键复用拒绝与3本入口Notebook、静态0变化；197项测试及162本全量Notebook是按未变身份继承的C2证据。本次未重新构建PDF或重跑这些实验。


## 目录排版修订（BIL23B5，2026-10-19）

在上述正式版首次提升之后，四册PDF仅修订目录显示：统一章号分隔，长标题按词换行，并为页码独立保留右侧空间。正文页的文字、72 dpi画面及链接目标逐页与B4比较；具体结果及独立审阅见项目当前接受登记。共用代码、配置、数据和Notebook未改，适用的执行证据继续沿用，未重新声称全量运行。
