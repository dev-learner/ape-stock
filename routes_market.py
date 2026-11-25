# routes_market.py
# Market data routes (quotes, sparkline, search, avg-volume, RSI) extracted from the original routes.py.

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify
from db import get_db
from data import fetch_quotes

UK = ZoneInfo("Europe/London")
bp = Blueprint("market", __name__)

@bp.route("/quotes", methods=["POST"])
def quotes():
    """Fetch live quotes for a list of symbols."""
    symbols = request.json.get("symbols", []) if request.is_json else []
    symbols = [s for s in symbols if isinstance(s, str) and s.strip()]
    return jsonify(fetch_quotes(symbols))

@bp.route("/sparkline/<symbol>")
def sparkline(symbol):
    """Return 5-minute price series for sparklines."""
    days = request.args.get("days", type=int)
    conn = get_db()
    cur = conn.cursor()
    if days and days > 1:
        cutoff = (datetime.now(UK) - timedelta(days=days)).isoformat()
        cur.execute("""
            SELECT price FROM snapshots_5min
            WHERE symbol = ? AND ts >= ?
            ORDER BY ts
        """, (symbol, cutoff))
    else:
        today = datetime.now(UK).date().isoformat()
        cur.execute("""
            SELECT price FROM snapshots_5min
            WHERE symbol = ? AND date(ts) = ?
            ORDER BY ts
        """, (symbol, today))
    rows = cur.fetchall()
    prices = [r["price"] for r in rows] if rows else []
    conn.close()
    if len(prices) > 1:
        return jsonify({"prices": prices, "mode": "5min"})
    return jsonify({"prices": [1, 1], "mode": "empty"})

@bp.route("/search")
def search():
    """Search FTSE and external constituents by symbol or name."""
    q = (request.args.get("q") or "").strip()
    if not q or len(q) < 1:
        return jsonify([])
    conn = get_db()
    cur = conn.cursor()
    like = f"%{q}%"
    upper = q.upper() + "%"

    # FTSE names
    cur.execute("""
        SELECT symbol, name, price, change_pct, 'FTSE' AS source
        FROM index_quotes
        WHERE symbol LIKE ? OR name LIKE ?
        ORDER BY 
            CASE WHEN symbol LIKE ? THEN 0 ELSE 1 END,
            symbol
        LIMIT 20
    """, (like, like, upper))
    ftse = [dict(r) for r in cur.fetchall()]

    # External names
    cur.execute("""
        SELECT symbol, name, NULL AS price, NULL AS change_pct, market AS source
        FROM external_constituents
        WHERE symbol LIKE ? OR name LIKE ?
        ORDER BY 
            CASE WHEN symbol LIKE ? THEN 0 ELSE 1 END,
            symbol
        LIMIT 15
    """, (like, like, upper))
    external = [dict(r) for r in cur.fetchall()]

    conn.close()

    # Merge, FTSE first, then external, dedupe by symbol
    seen = set()
    results = []
    for r in ftse + external:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            results.append(r)
        if len(results) >= 30:
            break

    return jsonify(results)

@bp.route("/avg-volume/<symbol>")
def avg_volume(symbol):
    """Return 30-day average volume from daily_closes, fallback to index_quotes."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(volume) FROM (
            SELECT volume FROM daily_closes
            WHERE symbol = ? AND volume IS NOT NULL
            ORDER BY date DESC LIMIT 30
        )
    """, (symbol,))
    row = cur.fetchone()
    avg = row[0] if row and row[0] else None
    if avg is None:
        cur.execute("SELECT avg_volume FROM index_quotes WHERE symbol = ?", (symbol,))
        row = cur.fetchone()
        avg = row["avg_volume"] if row else None
    conn.close()
    return jsonify({"avg_volume": avg})

@bp.route("/rsi/<symbol>")
def rsi(symbol):
    """Return RSI(7) from daily closes."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT close FROM daily_closes
        WHERE symbol = ? AND close IS NOT NULL
        ORDER BY date DESC LIMIT 30
    """, (symbol,))
    closes = [r[0] for r in cur.fetchall()][::-1]  # oldest first
    conn.close()
    if len(closes) < 8:
        return jsonify({"rsi7": None})

    def calc_rsi(prices, period=7):
        if len(prices) < period + 1:
            return None
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period-1) + gains[i]) / period
            avg_loss = (avg_loss * (period-1) + losses[i]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    return jsonify({"rsi7": round(calc_rsi(closes, 7), 1)})