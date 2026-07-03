# .bounty_stats.json 被外部覆写 (2026-06-03 17:33 cron tick)

## 现象

执行 `cat /opt/data/scripts/.bounty_stats.json` 得到：

```json
{
  "runs": [],
  "config": {
    "interval_minutes": 2,
    "start_time": null
  }
}
```

但 `smart_bounty_search.py` 的 `save_stats()` 输出格式是：

```json
{
  "runs": [
    {"time": "2026-06-03T17:30:00", "hour": 17}
  ]
}
```

## root cause

`config` 字段（`interval_minutes` + `start_time`）**不是**脚本中任何代码写的。说明 cron 调度器或外部的 wrapper 在每次 tick 开始时用模板覆写了这个文件，然后才执行脚本。这导致：

1. 脚本的 `save_stats()` 模块级调用（第380行）读取到的是空模板（`runs: []`），追加一条后写入
2. 但文件可能被调度器**再次覆写**（在脚本结束后，或者并行调度中）
3. 最终结果是所有统计数据丢失，只剩空模板

## 验证方法

```bash
# 查看 stats 文件元数据，确认创建者
ls -la /opt/data/scripts/.bounty_stats.json

# 搜索是谁写了 config 字段
grep -r "interval_minutes" /opt/hermes/cron/ /opt/hermes/hermes_cli/ 2>/dev/null

# 更直接的测试：运行脚本 2 次后检查
cd /opt/data/scripts && timeout 10 python3 smart_bounty_search.py 2>&1
cat .bounty_stats.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'runs count: {len(d.get(\"runs\",[]))}');"
```

## 修复

1. **将 `save_stats()` 移至 `main()` 结尾**，避免模块加载时过早记录；同时在 `main()` 开头也调用一次（记录本轮开始）
2. **或者改用独立文件**，如 `.bounty_stats_raw.json`，避免被调度器模板覆写
3. **或者确认调度器行为**：检查 `/opt/hermes/cron/scheduler.py` 中是否有对 stats 文件的写操作。如果有，方案改为在 `.bounty_history.json` 中附加统计字段
