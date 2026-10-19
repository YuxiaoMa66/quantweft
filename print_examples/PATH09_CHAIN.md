# PATH09：同一次 CLI → 只读 SQL 核账链

从包根执行，先按 README 建立环境。以下整个块替换旧第45章的孤立路径及 `r2-fixed-task` 常量；`run`、`state_db`、`run_key`必须贯穿同一次前置调用与查询。只读文件断言保留，缺库时拒绝，不创建空数据库。

```sh
run="runs/path09_$(.venv/bin/python -c 'from uuid import uuid4; print(uuid4().hex)')"
state_db="$run/state.db"
run_key="reader"
.venv/bin/python capstone/run_offline.py --config capstone/configs/offline_constructed.json --run-key "$run_key" --state-db "$state_db" --output-dir "$run/artifacts"
.venv/bin/python print_examples/I2-PATH-09.py "$state_db" "$run_key"
```

查询脚本使用 SQLite `mode=ro`，按同一个 `run_key` 查询两笔唯一成交，断言支出2004.002 USD、现金7995.998 USD。它保留原核账含义与只读边界，未新造撮合器；固定构造配置与共享核心不变。

I3若把 Python 查询块直接印入正文，须完整复制 `I2-PATH-09.py`，并保留 `state,key=Path(sys.argv[1]),sys.argv[2]` 的同链参数传递，不能只替换旧状态路径一行。PATH10–15的其他任务仍各用新目录/自己的显式任务键，不能混用PATH09结果。
