# scripts/gap_grid_search.py
# DESC: Grid-search gap size, volume window and forward days for recovery stats
# RUN: VENV

import sqlite3
from pathlib import Path
from collections import defaultdict

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT symbol, date, open, close, volume
    FROM daily_closes
    WHERE open IS NOT NULL AND close IS NOT NULL AND volume IS NOT NULL
    ORDER BY symbol, date
""")
rows = cur.fetchall()

by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(dict(r))

gap_thresholds = [4, 5, 6, 7, 8]
vol_windows = [20, 30, 50]
forward_days = [1, 3, 5]

print(f"{'Gap%':>5} {'VolWin':>6} {'Fwd':>4} {'Signals':>8} {'Recovered%':>11} {'AvgRet%':>8}")
print("-" * 50)

for gap in gap_thresholds:
    for win in vol_windows:
        for fwd in forward_days:
            signals = 0
            recovered = 0
            total_ret = 0.0
            for data in by_sym.values():
                if len(data) < win + fwd + 1:
                    continue
                for i in range(win, len(data) - fwd):
                    prev_c = data[i-1]["close"]
                    if not prev_c:
                        continue
                    gap_pct = (data[i]["open"] - prev_c) / prev_c * 100
                    if gap_pct > -gap:
                        continue
                    vols = [data[j]["volume"] for j in range(i-win, i)]
                    avg_vol = sum(vols) / len(vols) if vols else 0
                    if not avg_vol or data[i]["volume"] <= avg_vol:
                        continue
                    future_c = data[i+fwd]["close"]
                    if not future_c or not data[i]["open"]:
                        continue
                    ret = (future_c - data[i]["open"]) / data[i]["open"] * 100
                    signals += 1
                    total_ret += ret
                    if ret >= (gap * 0.5):
                        recovered += 1
            rec_pct = (recovered / signals * 100) if signals else 0
            avg_ret = (total_ret / signals) if signals else 0
            print(f"{gap:5} {win:6} {fwd:4} {signals:8} {rec_pct:10.1f}% {avg_ret:8.2f}")

conn.close()