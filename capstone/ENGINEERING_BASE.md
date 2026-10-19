# Capstone 工程基础规格与运行说明 (ENGINEERING_BASE)

\color{qink}


**状态**：`construction-only`（仅构造数据基线，无真实市场数据、无真实实盘/券商执行）。  
**版本**：`1.0.0` (A9-B Engineering Foundation Freeze)  
**配置冻结文件**：`capstone/configs/offline_constructed.json`

---

## 1. 范围与边界说明 (Scope & Invariants)

\color{qink}


1. **纯离线执行**：不连接外部网络，不调用任何在线金融 API 或券商下单接口，不请求任何外部秘钥或凭据。
2. **确定性构造数据集**：数据类型标为 `CONSTRUCTED_TEACHING_DATA`，包含两只教学资产（`AssetA`, `AssetB`）。
3. **因果与时点严格隔离**：
   - 特征与信号决策仅可读取 $\le \text{signal\_time}$ 的观测数据（`available_at`, `ingested_at`, `as_of`）。
   - 未来次日撮合（$09:00\text{Z}, 09:01\text{Z}$）与期末结算标记（$16:00\text{Z}$）仅供模拟器读取，严禁泄漏至特征与信号层。
4. **研究待办边界**：本阶段仅确立工程架构与质量闸门，18项研究报告中的策略发现与实盘检验均标为 `pending_A10`。

---

## 2. 当前读者包运行指令 (Portable Run Instructions)

\color{qink}


以下运行说明适用于完整课程包。恢复检查入口 `capstone/check_portable.py` 已按已接受I3只读来源逐字节恢复，可在包根直接运行。

从包根按[读者 README](../README.md)建立独立环境。每次生成新 `runs/` 子目录，使用原固定构造配置；目录、状态库与任务键在同一次调用中保持一致：

```sh
run="runs/ch45_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python code/ch45_production_quant.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"

run="runs/capstone_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
.venv/bin/python capstone/run_offline.py --config capstone/configs/offline_constructed.json --run-key reader --state-db "$run/state.db" --output-dir "$run/artifacts"
```

需要只读两笔成交及现金核账时，按[PATH09 完整链](../print_examples/PATH09_CHAIN.md)复用同一次状态库和任务键。已有恢复/幂等检查入口为 `capstone/check_portable.py`，本次文档适配不要求重复历史47项检查。

原 A9-B 版本将命令写到 `build/batches/A9-B/r2/...`；那些固定目录是**历史审计运行位置**，不是当前便携运行指令。原文来源及 SHA 在[便携历史接受摘要](ACCEPTED_ENGINEERING_VERSION.md)中保留。本文其余工程接口沿用，不改变原接受裁定、固定配置或18项研究模板。

---

## 3. 血缘、日志与持久状态接口 (Lineage & Logging Interface)

\color{qink}


### 3.1 SQLite 状态数据库表结构 (`state.db`)

\color{qink}


* `runs` 表：
  * `run_key TEXT PRIMARY KEY`: 任务唯一键。
  * `fingerprint TEXT NOT NULL`: 归一化输入、配置、代码哈希及历史模块哈希的 SHA-256 绑定指纹。
  * `status TEXT NOT NULL`: 运行状态（`RUNNING`, `STOPPED`, `COMPLETED`）。
  * `created_at TEXT`, `updated_at TEXT`, `output_dir TEXT`。
* `events` 表：
  * `id INTEGER PRIMARY KEY AUTOINCREMENT`: 自增事件序号。
  * `run_key TEXT`, `event_name TEXT`, `event_time TEXT`, `details_json TEXT`。
* `fills` 表：
  * `fill_id TEXT PRIMARY KEY`: 成交唯一键。
  * `run_key TEXT`, `order_id TEXT`, `parent_id TEXT`, `slot_index INTEGER`, `asset TEXT`, `fill_time TEXT`。
  * `signed_quantity REAL`, `mid_price REAL`, `fill_price REAL`, `notional REAL`。
  * `half_spread_usd REAL`, `temp_impact_usd REAL`, `perm_impact_usd REAL`, `commission REAL`。

### 3.2 幂等与故障恢复保证

\color{qink}


1. **同 Key 同输入**：读取已有成果与哈希，复用且不重复生成成交记录（稳定成交笔数）。
2. **同 Key 异输入**：拒绝执行，记录 `RUN_KEY_FINGERPRINT_MISMATCH` 事件。
3. **缓存篡改**：校验SQLite记录锚定的预期hash及 `checksums.json`，若被篡改显式拒绝，记录 `CACHED_ARTIFACT_CORRUPT`，严禁静默覆盖。
4. **中断恢复**：以已持久化的成交记录重建历史账本，避免二次扣款，继续未完成订单。
5. **风控/对账失败**：立即持久化 `STOPPED` 状态，阻止后续成交。

---

## 4. 商业产物与运行时切分 (Artifacts Structure)

\color{qink}


在 `--output-dir` 下原子发布以下文件：
* `business_summary.json`：确定性业务摘要（初始现金、期末现金、期末 NAV、毛/净 PnL、成本分解、独立对账状态）。
* `fills.csv`：成交流水表。
* `ledger_events.csv`：账本事件流水表。
* `signals_targets.csv`：信号与目标持仓表。
* `checksums.json`：业务文件的 SHA-256 校验和；SQLite同时锚定发布文件hash。
* `runtime_metadata.json`：运行耗时、开始/结束时间、进程 PID、环境信息等非确定性元数据。
* `report_evidence_interface.json`：18章研究证据接口定义（Capstone 入口生成）。
* `figures/`：图表（门禁结果指示图 `gate_outcomes.png`、现金与 NAV 演进图 `cash_nav_timeline.png`）。

* `normalized_inputs.json`、`normalized_config.json`、`lineage.json`：规范化输入、配置与版本血缘，全部绑定发布hash。结构化事件保存在SQLite events，运行stdout为JSON摘要；没有启动Python logging平台/Prometheus服务。图由CLI发布后生成，图不纳入核心缓存提交事务；正文图另存候选manifest。

恢复仅覆盖本批受控Python异常和本机SQLite/目录发布测试；未断电、未验分布式多进程、未运行真实券商模拟盘。Dockerfile为参考配置，镜像未构建、容器未运行，基础tag/未锁定依赖也不构成字节环境冻结。

`capstone/.dockerignore`是骨架参考；上述course-root构建的有效默认ignore应位于构建上下文根。本Dockerfile只COPY指定src/capstone/code，不COPY build或.venv，但此说明不代替镜像实际构建检查。

## R2限定返修接口

\color{qink}

金额容差1e−6 USD；固定配置股数有限正实数，非正信号目标0，算例整数，不校验券商lot size。观测/执行/估值资产集合一致，在状态创建前验证。压力简单收益≥−1，正冲击为一般情景允许，loss=−scenarioPnL可能为负。计算后非有限动量写FEATURE_VALIDATION_FAILED/STOPPED，0fills/不发布；终局独立对账失败写TERMINAL_RECONCILIATION_FAILED/STOPPED，保留原fills并拒绝重试。三种发布恢复：未发布新attempt；已发布有效补完成；已发布损坏拒绝。故障计累计实际成交次序，不绑定资产名；恢复不再注入第一笔已有成交，无足够正目标的指定故障在DB前拒绝。标签成熟后监控可在线更新，不能提前用未来标签；本批不运行模型监控。
