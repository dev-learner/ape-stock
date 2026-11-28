# scripts/calculate_recovery_score.py
# NAME: Calculate Recovery Score
# DESC: Computes a 0-100 Recovery score for every symbol and stores it.
# DETAIL: Identifies Recovery Screen candidates using current Settings, scores them by bounce percentile (higher bounce = higher score). Non-candidates receive 0. Safe to re-run.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: scores

"""
Calculate Recovery Score
------------------------
Produces a 0-100 recovery_score for every FTSE constituent.
Candidates (those passing the Recovery Screen criteria) are scored
by the percentile rank of their bounce from the post-high low.
Non-candidates receive 0.
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def get_setting(cur, key, default):
    """Read a setting, returning the default if missing or invalid."""
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    if row and row[0] is not None:
        try:
            return type(default)(row[0])
        except (TypeError, ValueError):
            pass
    return default

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure recovery_score column exists
    try:
        cur.execute("ALTER TABLE stock_scores ADD COLUMN recovery_score REAL")
    except sqlite3.OperationalError:
        pass

    # Recovery parameters from Settings
    lookback_months = int(get_setting(cur, "rec_lookback_months", 12))
    min_drawdown = float(get_setting(cur, "rec_min_drawdown", 35))
    min_bounce = float(get_setting(cur, "rec_min_bounce", 15))
    require_50ma = get_setting(cur, "rec_require_50ma", "1") == "1"
    min_mcap_m = float(get_setting(cur, "rec_min_mcap", 500))
    min_mcap = min_mcap_m * 1_000_000
    min_price_pence = float(get_setting(cur, "rec_min_price", 50))
    min_price = min_price_pence / 100.0

    print(f"Recovery params: lookback={lookback_months}m, drawdown>={min_drawdown}%, "
          f"bounce>={min_bounce}%, 50MA={require_50ma}, mcap>={min_mcap_m}m, price>={min_price_pence}p")

    # Price history
    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    # Market caps
    cur.execute("SELECT symbol, market_cap FROM index_quotes")
    meta = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

    cutoff = (datetime.now() - timedelta(days=lookback_months * 30)).strftime("%Y-%m-%d")
    candidates = []   # (symbol, bounce_pct)

    for sym, series in by_sym.items():
        if len(series) < 100:
            continue
        mcap = meta.get(sym)
        if min_mcap and (mcap or 0) < min_mcap:
            continue

        dates = [d for d, c in series]
        closes = [c for d, c in series]

        window = [(d, c) for d, c in series if d >= cutoff]
        if not window:
            continue
        high_date, high_price = max(window, key=lambda x: x[1])
        high_idx = dates.index(high_date)

        post_high = closes[high_idx:]
        if not post_high:
            continue
        low_price = min(post_high)
        drawdown_pct = (low_price / high_price - 1) * 100
        if drawdown_pct > -min_drawdown:
            continue

        current = closes[-1]
        if current < min_price:
            continue

        bounce_pct = (current / low_price - 1) * 100
        if bounce_pct < min_bounce:
            continue

        if require_50ma and len(closes) >= 50:
            ma50 = sum(closes[-50:]) / 50
            if current <= ma50:
                continue

        candidates.append((sym, bounce_pct))

    print(f"Found {len(candidates)} recovery candidates")

    # Percentile score among candidates (higher bounce = higher score)
    if candidates:
        bounces = sorted([b for _, b in candidates])
        n = len(bounces)

        def to_score(bounce):
            # percentile rank 0-100
            rank = sum(1 for b in bounces if b <= bounce)
            return round(100.0 * rank / n, 1)
    else:
        def to_score(_):
            return 0.0

    # Build full score map (candidates get percentile, everyone else 0)
    score_map = {sym: to_score(bounce) for sym, bounce in candidates}
    all_symbols = set(by_sym.keys())

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for sym in all_symbols:
        score = score_map.get(sym, 0.0)
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, recovery_score)
            VALUES (?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET
                recovery_score = excluded.recovery_score
        """, (sym, today, score))
        count += 1

    conn.commit()
    conn.close()
    print(f"Recovery scores written for {count} symbols on {today}.")
    if candidates:
        print("Top 10 candidates by bounce:")
        for sym, bounce in sorted(candidates, key=lambda x: -x[1])[:10]:
            print(f"  {sym:<8} bounce={bounce:5.1f}%  score={score_map[sym]:5.1f}")

if __name__ == "__main__":
    main()