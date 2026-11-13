# scripts/gap_down_volume.py
# DESC: Count high-volume gap-downs (≥5 %) and show samples
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Load all daily data ordered by symbol, date
cur.execute("""
    SELECT symbol, date, open, close, volume
    FROM daily_closes
    WHERE open IS NOT NULL AND close IS NOT NULL AND volume IS NOT NULL
    ORDER BY symbol, date
""")
rows = cur.fetchall()

# Group by symbol
by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(r)

GAP_PCT = 5.0          # open 5% below previous close
VOL_WINDOW = 30        # 30-day average volume

total_gaps = 0
gaps_with_high_vol = 0
examples = []

for sym, data in by_sym.items():
    if len(data) < VOL_WINDOW + 1:
        continue
    for i in range(VOL_WINDOW, len(data)):
        prev_close = data[i-1]["close"]
        today_open = data[i]["open"]
        today_vol = data[i]["volume"]
        if prev_close is None or prev_close == 0:
            continue
        gap_pct = (today_open - prev_close) / prev_close * 100
        if gap_pct <= -GAP_PCT:
            # 30-day average volume up to yesterday
            vols = [data[j]["volume"] for j in range(i-VOL_WINDOW, i) if data[j]["volume"]]
            if not vols:
                continue
            avg_vol = sum(vols) / len(vols)
            total_gaps += 1
            high_vol = today_vol > avg_vol
            if high_vol:
                gaps_with_high_vol += 1
            if len(examples) < 15:
                examples.append((sym, data[i]["date"], round(gap_pct, 2), today_vol, int(avg_vol), high_vol))

print(f"Gap-downs >= {GAP_PCT}% (open vs prev close): {total_gaps}")
print(f"Of which volume > 30-day average: {gaps_with_high_vol}")
if total_gaps:
    print(f"Percentage: {gaps_with_high_vol / total_gaps * 100:.1f}%")
print("\nSample occurrences:")
for e in examples:
    flag = "HIGH VOL" if e[5] else ""
    print(f"  {e[0]:<10} {e[1]}  gap {e[2]:>6.2f}%  vol {e[3]:>10,}  avg {e[4]:>10,}  {flag}")

conn.close()