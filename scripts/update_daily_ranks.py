# scripts/update_daily_ranks.py
# NAME: Update Daily Ranks
# DESC: Computes and stores daily persistence ranks for the Screener.
# DETAIL: Ranks every symbol that has daily closes by how often it appeared in the top-N of the Screener over the configured window. Results are written to the daily_ranks table (one row per symbol for the latest date). Automatically run by the application when ranks are stale. Safe to run manually. Does not delete historical ranks for previous dates.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: scores

"""
Update Daily Ranks
------------------
Builds a daily ranking of FTSE constituents based on persistence in the
Screener (Tool 4).

For each trading day in the look-back window the script reconstructs the
Screener universe (above 50- & 200-day MAs, positive 3-month return,
market-cap floor) and counts how many times each symbol appeared in the
top-N (rank_cutoff). The final ranking is ordered by that count.

Results are stored in daily_ranks for the most recent date only.
The script is called automatically from app.py when the stored timestamp
is older than the configured threshold.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"
UK = ZoneInfo("Europe/London")

def get_setting(conn, key, default):
    """Read a single value from app_settings, returning the default if missing."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else default

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ranking parameters from Settings
    window = int(get_setting(conn, "rank_window", "35"))
    min_pct = float(get_setting(conn, "rank_presence", "50"))
    cutoff = int(get_setting(conn, "rank_cutoff", "12"))

    print(f"Ranking with window={window}, presence={min_pct}%, cut-off={cutoff}")

    # Load all daily closes
    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    all_dates = set()
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], r["close"]))
        all_dates.add(r["date"])

    # Market-cap lookup for the size filter
    cur.execute("SELECT symbol, market_cap FROM index_quotes")
    meta = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

    universe = set(by_sym.keys())
    sorted_dates = sorted(all_dates)
    if not sorted_dates:
        print("No daily closes.")
        conn.close()
        return

    today = sorted_dates[-1]
    print(f"Ranking as of {today} ({len(universe)} symbols)")

    def build_screener(as_of):
        """Return the ordered list of symbols that pass Screener rules on a given date."""
        cands = []
        for sym, series in by_sym.items():
            closes = [c for d, c in series if d <= as_of]
            n = len(closes)
            if n < 200:
                continue
            ret_3m = (closes[-1] / closes[-63] - 1) * 100 if n > 63 and closes[-63] else None
            if ret_3m is None or ret_3m <= -15:
                continue
            ma50 = sum(closes[-50:]) / 50
            ma200 = sum(closes[-200:]) / 200
            if closes[-1] <= ma50 or closes[-1] <= ma200:
                continue
            mcap = meta.get(sym)
            if mcap is not None and mcap < 2_000_000_000:
                continue
            cands.append((sym, ret_3m))
        cands.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in cands]

    # Count appearances in the top-N over the trailing window
    from_idx = max(0, len(sorted_dates) - window)
    window_dates = sorted_dates[from_idx:]
    scores = defaultdict(int)

    for d in window_dates:
        top = build_screener(d)[:cutoff]
        for sym in top:
            scores[sym] += 1

    # Ensure every symbol receives a score (0 if it never appeared)
    for sym in universe:
        if sym not in scores:
            scores[sym] = 0

    # Rank by score descending, then symbol for stability
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    needed = max(1, int(window * min_pct / 100.0))

    # Replace today's ranks only
    cur.execute("DELETE FROM daily_ranks WHERE date = ?", (today,))
    for rank, (sym, sc) in enumerate(ranked, 1):
        cur.execute("""
            INSERT INTO daily_ranks (symbol, date, rank, score, persistence_days)
            VALUES (?, ?, ?, ?, ?)
        """, (sym, today, rank, float(sc), sc))

    conn.commit()
    print(f"Wrote {len(ranked)} ranks for {today} (threshold {needed} days)")
    print("Top 12:")
    for rank, (sym, sc) in enumerate(ranked[:12], 1):
        flag = " *" if sc >= needed else ""
        print(f"  {rank:2}. {sym:<8} {sc} days{flag}")
    print(f"... lowest rank: {ranked[-1][0]} (score {ranked[-1][1]})")

    # Record timestamp
    now = datetime.now(UK).isoformat()
    cur.execute("""
        INSERT INTO app_settings (key, value)
        VALUES ('ranks_updated', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (now,))
    conn.commit()

    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()