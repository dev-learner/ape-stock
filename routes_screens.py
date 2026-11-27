# routes_screens.py
# Tool 12 — Screeners
# - /screens/composite  → full universe ordered by composite_score + 1-year prices
# - /screens/recovery   → Recovery Screen (used by Tool 4 & Tool 6)

from datetime import datetime, timedelta
from collections import defaultdict
from flask import Blueprint, jsonify
from db import get_db, get_setting

bp = Blueprint("screens", __name__)

@bp.route("/screens/composite")
def composite_screen():
    """Return all symbols ordered by latest composite_score (best first).
    Includes component ranks, scores, and a 1-year price series for sparklines.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            s.symbol,
            q.name,
            q.sector,
            q.price,
            q.change_pct,
            s.base_rank,
            s.base_score,
            s.ta_rank,
            s.ta_score,
            s.fund_rank,
            s.fund_score,
            s.composite_score,
            s.composite_rank
        FROM stock_scores s
        LEFT JOIN index_quotes q ON q.symbol = s.symbol
        WHERE s.score_date = (SELECT MAX(score_date) FROM stock_scores)
          AND s.composite_rank IS NOT NULL
        ORDER BY s.composite_rank ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append(float(r["close"]))

    for row in rows:
        series = by_sym.get(row["symbol"], [])
        row["prices"] = series[-252:] if series else []

    conn.close()
    return jsonify({
        "screen": "composite",
        "count": len(rows),
        "rows": rows
    })


@bp.route("/screens/recovery")
def recovery_screen():
    """Return Recovery Screen candidates using Settings values.
    Applies min-price guard and returns 1-year price series + key indices.
    Used by Tool 4 and Tool 6.
    """
    try:
        lookback_months = int(get_setting("rec_lookback_months", "12"))
    except (TypeError, ValueError):
        lookback_months = 12

    try:
        min_drawdown = float(get_setting("rec_min_drawdown", "35"))
    except (TypeError, ValueError):
        min_drawdown = 35.0

    try:
        min_bounce = float(get_setting("rec_min_bounce", "15"))
    except (TypeError, ValueError):
        min_bounce = 15.0

    require_50ma = get_setting("rec_require_50ma", "1") == "1"

    try:
        min_mcap_m = float(get_setting("rec_min_mcap", "500"))
        min_mcap = min_mcap_m * 1_000_000
    except (TypeError, ValueError):
        min_mcap = 500_000_000

    try:
        min_price_pence = float(get_setting("rec_min_price", "50"))
        min_price = min_price_pence / 100.0
    except (TypeError, ValueError):
        min_price = 0.50

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    cur.execute("SELECT symbol, market_cap, name FROM index_quotes")
    meta = {r["symbol"]: {"mcap": r["market_cap"], "name": r["name"]} for r in cur.fetchall()}

    cur.execute("SELECT MAX(date) FROM daily_ranks")
    rank_date = cur.fetchone()[0]
    ranks = {}
    if rank_date:
        cur.execute("SELECT symbol, rank FROM daily_ranks WHERE date = ?", (rank_date,))
        ranks = {r["symbol"]: r["rank"] for r in cur.fetchall()}

    cutoff = (datetime.now() - timedelta(days=lookback_months * 30)).strftime("%Y-%m-%d")
    candidates = []

    for sym, series in by_sym.items():
        if len(series) < 100:
            continue
        info = meta.get(sym, {})
        if min_mcap and (info.get("mcap") or 0) < min_mcap:
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
        low_idx = high_idx + post_high.index(low_price)
        low_date = dates[low_idx]
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

        series_start = max(0, len(series) - 252)
        price_series = closes[series_start:]
        series_dates = dates[series_start:]

        def find_idx(target_date):
            try:
                return series_dates.index(target_date)
            except ValueError:
                return None

        high_series_idx = find_idx(high_date)
        low_series_idx = find_idx(low_date)
        current_series_idx = len(price_series) - 1 if price_series else None

        candidates.append({
            "symbol": sym,
            "name": (info.get("name") or "")[:28],
            "high_date": high_date,
            "high_price": round(high_price, 2),
            "low_date": low_date,
            "low_price": round(low_price, 2),
            "drawdown_pct": round(drawdown_pct, 1),
            "bounce_pct": round(bounce_pct, 1),
            "current": round(current, 2),
            "rank": ranks.get(sym),
            "prices": price_series,
            "high_idx": high_series_idx,
            "low_idx": low_series_idx,
            "current_idx": current_series_idx
        })

    candidates.sort(key=lambda x: x["bounce_pct"], reverse=True)
    conn.close()

    return jsonify({
        "screen": "recovery",
        "count": len(candidates),
        "rows": candidates
    })