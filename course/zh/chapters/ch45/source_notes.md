# 第45章：参考资料

本页列出本章相关的论文、课程、数据来源与工具文档。

<a id="opened-source-documents"></a>

### PANDAS

[pandas documentation](https://pandas.pydata.org/docs/)

### SK_PITFALLS

[scikit-learn Common pitfalls and recommended practices](https://scikit-learn.org/stable/common_pitfalls.html)

### CH45_PYPA_PACKAGING

[Python Packaging Authority. *Packaging Python Projects*.](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

### CH45_PY_LOGGING

[Python Software Foundation. *Logging HOWTO (Python 3 Documentation)*.](https://docs.python.org/3/howto/logging.html)

### CH45_PARQUET_OVERVIEW

[Apache Software Foundation. *Apache Parquet Documentation: Overview*.](https://parquet.apache.org/docs/overview/)

### CH45_DOCKERFILE

[Docker Inc. *Dockerfile reference and concepts*.](https://docs.docker.com/build/concepts/dockerfile/)

### CH45_DUCKDB_PARQUET

[DuckDB Foundation. *DuckDB Parquet Overview and Partial Reading*.](https://duckdb.org/docs/current/data/parquet/overview)

### CH45_PY314_SQLITE

[Python Software Foundation. *sqlite3 — DB-API 2.0 interface for SQLite databases (Python 3.14 Documentation)*.](https://docs.python.org/3.14/library/sqlite3.html)

### CH45_PY314_OS_REPLACE

[Python Software Foundation. *os.replace (Python 3.14 Documentation)*.](https://docs.python.org/3.14/library/os.html)

### CH45_12FACTOR_CONFIG

[Adam Wiggins. *The Twelve-Factor App: III. Config*.](https://12factor.net/config)

### CH45_PYTEST_DOCS

[Holger Krekel et al. *pytest: Simple powerful testing with Python*.](https://docs.pytest.org/en/stable/)

### CH45_SQLITE_TRANSACTIONS

[D. Richard Hipp et al. *SQLite Language: Transaction Control*.](https://www.sqlite.org/lang_transaction.html)

### CH45_AIRFLOW_DAGRUN

[Apache Software Foundation. *Apache Airflow: DAG Runs*.](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)

### CH45_PROMETHEUS_METRICS

[Prometheus Authors. *Prometheus Metric Types*.](https://prometheus.io/docs/concepts/metric_types/)

### CH45_MLFLOW_TRACKING

[MLflow Documentation. *Tracking APIs*.](https://mlflow.org/docs/latest/ml/tracking/tracking-api/)

### CH45_SEC_KNIGHT_CAPITAL

[U.S. Securities and Exchange Commission. *In the Matter of Knight Capital Americas LLC (Release No. 34-70694)*.](https://www.sec.gov/litigation/admin/2013/34-70694.pdf)

### CH45_PYPA_SRC_LAYOUT

[Discussions: src-layout vs flat-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

src-layout 讨论项目文件与可导入源码包的分离，并强调明确测试路径。

### CH45_PY314_LOGGING_COOKBOOK

[Logging Cookbook (Python 3.14 Documentation)](https://docs.python.org/3.14/howto/logging-cookbook.html)

标准 FileHandler 不会串行化多个进程对同一文件的写入。本书示例为单进程、每次运行使用独立日志，不代表分布式日志平台。

### CH45_DOCKER_SECRETS

[Docker Build Secrets](https://docs.docker.com/build/building/secrets/)

构建秘密不应通过 ARG 或 ENV 传递；secret mount 具有独立生命周期。构建凭据与运行时凭据需要区分。

### CH45_PY314_SCHED

[sched — Event scheduler (Python 3.14 Documentation)](https://docs.python.org/3.14/library/sched.html)

Python sched 是进程内事件调度器，调用 run() 才会执行队列；它不提供系统级服务、持久任务、交易日历、重试或幂等机制。

### CH45_PY314_URLLIB

[urllib.request — Extensible library for opening URLs (Python 3.14 Documentation)](https://docs.python.org/3.14/library/urllib.request.html)

HTTP 响应可用不等于数据契约、许可或历史点时完整性。

### CH45_GOOGLE_ML_RULES

[Rules of Machine Learning: Best Practices for ML Engineering](https://developers.google.com/machine-learning/guides/rules-of-ml)

这里讨论的是一般机器学习实践，不是金融 Alpha 实证证据，也不授权自动重训。

### CH45_R2_KS

[ks_2samp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html)

ks_2samp 的双侧统计量是两条经验分布函数的最大差异；其经典 p 值假设样本独立且连续，不适用于本例四行离散或自相关数据。

### CH45_R2_PSI

[risk.validation.populationStabilityIndex](https://www.mathworks.com/help/risk/risk.validation.populationstabilityindex.html)

PSI 的经验阈值不是普遍保证。

### CH45_R2_PH

[PageHinkley](https://riverml.xyz/dev/api/drift/PageHinkley/)

固定基线单侧 Page-Hinkley 教学规则不同于运行均值、遗忘因子或双侧更新。

### CH45_R2_SRC

[src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

src-layout 讨论包发现、安装关系与显式 CLI 路径。

### CH45_R2_PEP517

[PEP 517](https://peps.python.org/pep-0517/)

PEP 517 未强制规定项目目录布局。

### CH45_R2_PEP518

[PEP 518](https://peps.python.org/pep-0518/)

PEP 518 说明 build-system 声明。

[章节正文](content.md) · [完整参考资料](../../../../editions/zh/resources/references.md)
