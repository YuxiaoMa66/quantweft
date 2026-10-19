# 量化金融与系统化研究 · Quantitative Finance and Systematic Research

Yuxiao Ma · 本地正式版 / local formal edition (2026-10-19)

- **中文**：从[中文入口](editions/zh/README.md)开始——[完整正文PDF](editions/zh/body/main.pdf) · [完整Loom PDF](editions/zh/loom/main.pdf) · [Notebook导读](editions/zh/NOTEBOOK_GUIDE.md)
- **English**: start at the [English entry](editions/en/README.md) — [complete body PDF](editions/en/body/main.pdf) · [complete Loom PDF](editions/en/loom/main.pdf) · [Notebook guide](editions/en/NOTEBOOK_GUIDE.md)

两种语言共用同一套代码、数据、配置与运行器（本目录根下的`src/`、`code/`、`tests/`、`projects/`、`capstone/`、`run_notebook.py`和锁文件）；只有文字与Notebook的Markdown分语言。The two languages share one implementation (code, data, configuration, and runner at this root); only prose and Notebook Markdown differ by language.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/zh/notebooks/ch35_execution_ledger_constructed.ipynb
.venv/bin/python run_notebook.py editions/en/notebooks/ch35_execution_ledger_constructed.ipynb
```

验证范围 / validation scope: [中文](editions/zh/LOCAL_VALIDATION.md) · [English](editions/en/LOCAL_VALIDATION.md). 默认离线；不含市场数据，真实市场研究未执行。Offline by default; no market data is bundled and real-market research has not been run.


2026-10-19目录排版修订：四册目录统一章号分隔，长标题按词换行，页码固定右对齐。教学内容及共用实现沿用已接受版本。
