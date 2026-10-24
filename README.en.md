<p align="right"><a href="README.md">简体中文</a> | <strong>English</strong></p>

![QuantWeft by Yuxiao Ma](docs/assets/quantweft-cover.png)

# QuantWeft

**A Bilingual Course in Quantitative Finance and Systematic Research** · 45 chapters · 6 projects · 1 Capstone

**[Open the web reader →](https://quantweft.yuxiao.win/read/en/)**　Full-text search · Same-chapter language switching · Night mode

## Download the PDFs

| | English | 中文 |
| :--- | :--- | :--- |
| **Textbook** | [Textbook](editions/en/body/quantweft-textbook-en.pdf) | [中文正文](editions/zh/body/quantweft-textbook-zh.pdf) |
| **Workbook** (with full answers) | [Workbook](editions/en/workbook/quantweft-workbook-en.pdf) | [中文练习册](editions/zh/workbook/quantweft-workbook-zh.pdf) |

Read the textbook, attempt the workbook on your own, then run the Notebooks to check calculations and outputs.

## Learning route

**Mathematical and financial foundations → Statistical models and asset pricing → Strategy testing and research engineering**

Begin with Python, data, and timing contracts. Progress through regression, optimization, time series, and portfolios to out-of-sample validation, risk, costs, execution, and financial machine learning.

[English learning guide](editions/en/README.md) · [Curriculum](editions/en/resources/syllabus.md) · [Learning route](editions/en/resources/learning_roadmap.md) · [Chapter dependency graph](editions/en/resources/dependency_graph.md)

## Connect ideas through projects

| Foundational applications | Strategy research |
| :--- | :--- |
| [Financial data analysis](editions/en/projects/project01/README.md): returns, wealth, volatility, and drawdown | [Multi-factor equity strategy](editions/en/projects/project04/README.md): signals, universes, costs, and robustness |
| [CAPM and Fama-French](editions/en/projects/project02/README.md): regression, exposure, and inference | [Pairs trading](editions/en/projects/project05/README.md): training-window selection and out-of-sample ledgers |
| [Portfolio optimization](editions/en/projects/project03/README.md): rolling estimation and baseline comparison | [Machine-learning alpha](editions/en/projects/project06/README.md): date-based splits, baselines, and stability |

The [Capstone](editions/en/capstone/README.md) connects the research question, timing contracts, protocol, execution, and report. Negative results can pass; market research has separate data and authorization gates.

## Run your first Notebook

Both languages share code, data contracts, dependencies, and a runner. Notebook code cells are identical.

Run these commands from the **repository root**. The project declares Python ≥ 3.12; this lock file targets the checked **macOS arm64 / CPython 3.14.7** environment. Other platforms have not been validated.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-macos-arm64-py314.lock
.venv/bin/python -m ipykernel install --prefix .venv --name python3 --display-name 'Reader Python'
.venv/bin/python run_notebook.py editions/en/notebooks/ch35_execution_ledger_constructed.ipynb
```

This is Chapter 35's constructed execution-ledger example. Dependency installation may use the network; default teaching execution is offline. The [Chinese Notebook](editions/zh/notebooks/ch35_execution_ledger_constructed.ipynb) runs the same code. See the [Notebook guide](editions/en/NOTEBOOK_GUIDE.md) for more.

## Keep exploring

[Glossary](editions/en/resources/glossary.md) · [Notation and units](editions/en/resources/notation.md) · [References](editions/en/resources/references.md) · [Chapter texts](course/README.md) · [File navigation](editions/en/FILE_TREE.md) · [Repository guide](docs/README.md) · [Website and build](docs/SITE.md)

<details>
<summary>Edition, validation scope, and publication status</summary>

See [Local validation scope](editions/en/LOCAL_VALIDATION.md) for the runtime environment and compatibility.

The default route uses constructed data. French market data are not distributed, and real-market research has not been run. Historical results and unresolved evidence gaps retain their recorded scope; see [Remaining work](editions/en/REMAINING_ITEMS.md) and [Optional data contracts](editions/en/OPTIONAL_DATA.md).

By **Yuxiao Ma**. Original code uses **MIT**; author-controlled original educational content uses **CC BY-NC-SA 4.0** for non-commercial use. Commercial use requires separate permission. See [license scope and third-party exceptions](LICENSE.md). The repository is public; the [rights review](docs/legal/RIGHTS_REVIEW.md) is ongoing. See [Repository scope and provenance](docs/maintenance/REPOSITORY_STATUS.md).

</details>

## Exercise design credit

Parts of the workbook’s exercise design and layout draw on the [loom-notes](https://github.com/Polaris-Aeterna/loom-notes) LaTeX template, selectively adapted to the course. The template is not used in full. See [Attribution and acknowledgements](docs/legal/ACKNOWLEDGEMENTS.md).

## Contribute and support

Spotted a mistake or have an idea? [Send learning feedback](https://github.com/YuxiaoMa66/quantweft/issues/new?template=feedback.yml) or read the [contribution guide](.github/CONTRIBUTING.md). If the course is useful, a Star or a share with someone learning quant helps others find it.

The course is free to read and use. If it has helped you, proofreading, sharing or sponsoring keeps it maintained and updated. Sponsor on [GitHub Sponsors](https://github.com/sponsors/YuxiaoMa66) or use the WeChat Pay and Alipay codes below; any amount helps. See [support details](.github/SUPPORT.md).

<details>
<summary>Support with WeChat Pay / Alipay · View QR codes</summary>

Verify the recipient in the corresponding app. Open either image for the original size. The repository does not process payments; availability depends on the provider.

| WeChat Pay | Alipay |
| --- | --- |
| [![WeChat Pay support QR](docs/assets/support/wechat-pay.jpg)](docs/assets/support/wechat-pay.jpg) | [![Alipay support QR](docs/assets/support/alipay.jpg)](docs/assets/support/alipay.jpg) |

</details>
