# scripts/update_screener_metrics.py
# DESC: Compute and store screener metrics (returns, MAs, volatility, sector-relative) for all constituents
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
import math

UK = ZoneInfo("Europe/London")
db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=60)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Ensure columns exist
columns = [
    ("ret_3m", "REAL"), ("ret_6m", "REAL"), ("dist_52w_high", "REAL"),
    ("above_50ma", "INTEGER"), ("pct_from_50ma", "REAL"),
    ("above_200ma", "INTEGER"), ("pct_from_200ma", "REAL"),
    ("vol_20d", "REAL"), ("sector_rel_1d", "REAL"), ("sector_rel_5d", "REAL"),
]
for col, typ in columns:
    try:
        cur.execute(f"ALTER TABLE index_quotes ADD COLUMN {col} {typ}")
    except sqlite3.OperationalError:
        pass
conn.commit()

print("Loading daily closes...")
cur.execute("""
    SELECT symbol, date, close
    FROM daily_closes
    WHERE close IS NOT NULL
    ORDER BY symbol, date
""")
by_sym = defaultdict(list)
for r in cur.fetchall():
    by_sym[r["symbol"]].append(r["close"])

print("Loading sectors...")
cur.execute("SELECT symbol, sector FROM index_quotes WHERE sector IS NOT NULL")
sectors = {r["symbol"]: r["sector"] for r in cur.fetchall()}

print("Computing...")
updates = []
sector_1d = defaultdict(list)
sector_5d = defaultdict(list)

for sym, closes in by_sym.items():
    n = len(closes)
    if n < 30:
        continue

    ret_3m = (closes[-1] / closes[-63] - 1) * 100 if n > 63 and closes[-63] else None
    ret_6m = (closes[-1] / closes[-126] - 1) * 100 if n > 126 and closes[-126] else None

    lookback = min(252, n)
    high_52w = max(closes[-lookback:])
    dist_52w = (closes[-1] / high_52w - 1) * 100 if high_52w else None

    def sma(p):
        return sum(closes[-p:]) / p if n >= p else None

    ma50 = sma(50)
    ma200 = sma(200)
    above_50 = 1 if ma50 and closes[-1] > ma50 else 0
    pct_50 = (closes[-1] / ma50 - 1) * 100 if ma50 else None
    above_200 = 1 if ma200 and closes[-1] > ma200 else 0
    pct_200 = (closes[-1] / ma200 - 1) * 100 if ma200 else None

    vol_20d = None
    if n >= 21:
        rets = [(closes[i] / closes[i-1] - 1) for i in range(n-20, n) if closes[i-1]]
        if rets:
            mean = sum(rets) / len(rets)
            var = sum((r - mean)**2 for r in rets) / len(rets)
            vol_20d = math.sqrt(var) * 100

    ret_1d = (closes[-1] / closes[-2] - 1) * 100 if n >= 2 and closes[-2] else None
    ret_5d = (closes[-1] / closes[-6] - 1) * 100 if n >= 6 and closes[-6] else None

    sector = sectors.get(sym)
    if sector and ret_1d is not None:
        sector_1d[sector].append(ret_1d)
    if sector and ret_5d is not None:
        sector_5d[sector].append(ret_5d)

    updates.append((
        ret_3m, ret_6m, dist_52w,
        above_50, pct_50, above_200, pct_200,
        vol_20d, None, None,
        sym, ret_1d, ret_5d, sector
    ))

avg_1d = {s: sum(v)/len(v) for s, v in sector_1d.items() if v}
avg_5d = {s: sum(v)/len(v) for s, v in sector_5d.items() if v}

print(f"Writing {len(updates)} rows...")
batch = []
for u in updates:
    ret_3m, ret_6m, dist_52w, above_50, pct_50, above_200, pct_200, vol_20d, _, _, sym, ret_1d, ret_5d, sector = u
    rel_1d = (ret_1d - avg_1d[sector]) if sector and ret_1d is not None and sector in avg_1d else None
    rel_5d = (ret_5d - avg_5d[sector]) if sector and ret_5d is not None and sector in avg_5d else None
    batch.append((
        ret_3m, ret_6m, dist_52w,
        above_50, pct_50, above_200, pct_200,
        vol_20d, rel_1d, rel_5d, sym
    ))

cur.executemany("""
    UPDATE index_quotes
    SET ret_3m=?, ret_6m=?, dist_52w_high=?,
        above_50ma=?, pct_from_50ma=?,
        above_200ma=?, pct_from_200ma=?,
        vol_20d=?, sector_rel_1d=?, sector_rel_5d=?
    WHERE symbol=?
""", batch)

# Record timestamp
now = datetime.now(UK).isoformat()
cur.execute("""
    INSERT INTO app_settings (key, value)
    VALUES ('screener_metrics_updated', ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
""", (now,))

conn.commit()
conn.close()
print("Done. Screener metrics updated.")