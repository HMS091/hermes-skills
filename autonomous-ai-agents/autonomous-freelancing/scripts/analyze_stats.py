#!/opt/hermes/.venv/bin/python3
"""分析 Bounty Stats，生成 2分钟 vs 5分钟 对比报告"""
import json, os
from datetime import datetime, timezone

STATS_FILE = "/opt/data/scripts/.bounty_stats.json"
HISTORY_FILE = "/opt/data/scripts/.bounty_history.json"

def analyze():
    if not os.path.exists(STATS_FILE):
        print("❌ 还没有统计数据，等跑完一轮再来")
        return

    with open(STATS_FILE) as f:
        stats = json.load(f)

    runs = stats.get("runs", [])
    if not runs:
        print("❌ 无运行记录")
        return

    start = runs[0]["time"]
    end = runs[-1]["time"]

    # 计算 PR 提交数
    prs_done = 0
    prs_list = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            hist = json.load(f)
        for url, v in hist.items():
            if "PR #" in v:
                prs_done += 1
                prs_list.append(f"  {url} → {v}")

    total_runs = len(runs)
    duration_h = total_runs * 2 / 60 if total_runs > 0 else 0

    print(f"""
╔══════════════════════════════════════════════╗
║        Bounty 搜索效率分析报告                ║
╚══════════════════════════════════════════════╝

📅 时间段: {start} ~ {end}
🔄 总运行次数: {total_runs} 次
⏱  每次间隔: 2 分钟
⏳ 总耗时: ~{duration_h:.1f} 小时

📊 执行结果:
   ✅ 历史 PR 总数: {prs_done} 个
""")

    if prs_list:
        print("   已提交 PR:")
        for p in prs_list:
            print(p)

    print(f"""
📈 2分钟 vs 5分钟 对比:
   如果用 5分钟间隔 (同样 {duration_h:.1f} 小时): {total_runs * 2 / 5:.0f} 次
   如果用 2分钟间隔 (同样 {duration_h:.1f} 小时): {total_runs} 次
   2分钟比5分钟多跑: {total_runs - total_runs * 2 / 5:.0f} 次 ({((1-2/5)*100):.0f}% 更多)

💡 结论:
   2分钟 vs 5分钟的关键差异:
   - 2分钟: 更早发现新单，抢单更快，但 API 压力更大
   - 5分钟: 省 API 配额，但可能漏掉先到先得的单子

   如果整晚抢到真正能变现的 PR → 2分钟更好
   如果和之前5分钟一样没有真钱单 → 5分钟就够了
""")

if __name__ == "__main__":
    analyze()
