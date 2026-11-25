# routes_tools.py
# Tool dispatcher (currently Tool 8) extracted from the original routes.py.

from flask import Blueprint, request, jsonify
from db import get_db, get_setting
from routes_core import get_index_data

bp = Blueprint("tools", __name__)

@bp.route("/tool/<int:tool_id>", methods=["POST"])
def run_tool(tool_id):
    """Dispatcher for tool endpoints. Currently handles Tool 8 (Risers/Fallers)."""
    data = request.get_json(silent=True) or {}
    
    if tool_id == 8:
        # --- Limit from Settings (supports "all") ---
        raw_limit = get_setting("listLimit", None)
        if raw_limit is None:
            raw_limit = data.get("limit") or 25

        if str(raw_limit).lower() == "all":
            limit = None                       # no LIMIT clause
        else:
            try:
                limit = int(raw_limit)
                if limit < 1:
                    limit = 25
            except (TypeError, ValueError):
                limit = 25

        # --- % thresholds from Settings ---
        try:
            riser_pct = float(get_setting("riserPct", "0"))
        except (TypeError, ValueError):
            riser_pct = 0.0
        try:
            faller_pct = float(get_setting("fallerPct", "0"))
        except (TypeError, ValueError):
            faller_pct = 0.0

        risers_index = data.get("risers_index") or "ALL"
        fallers_index = data.get("fallers_index") or "ALL"

        # get_index_data must accept limit=None meaning "no limit"
        risers = get_index_data(risers_index, "gainers", limit, min_change=riser_pct)
        fallers = get_index_data(fallers_index, "losers", limit, max_change=-faller_pct)

        def enrich(rows):
            conn = get_db()
            cur = conn.cursor()
            for r in rows:
                sym = r["symbol"]
                cur.execute("""
                    SELECT AVG(volume) FROM (
                        SELECT volume FROM daily_closes
                        WHERE symbol = ? AND volume IS NOT NULL
                        ORDER BY date DESC LIMIT 30
                    )
                """, (sym,))
                avg_row = cur.fetchone()
                r["avg_volume"] = avg_row[0] if avg_row and avg_row[0] else r.get("avg_volume")

                cur.execute("""
                    SELECT close FROM daily_closes
                    WHERE symbol = ? AND close IS NOT NULL
                    ORDER BY date DESC LIMIT 60
                """, (sym,))
                closes = [row[0] for row in cur.fetchall()][::-1]

                # RSI using settings
                try:
                    rsi_len = int(get_setting("rsiLength", "7"))
                    rsi_len = max(1, min(30, rsi_len))
                except (TypeError, ValueError):
                    rsi_len = 7

                r["rsi7"] = None
                if len(closes) >= rsi_len + 1:
                    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
                    gains = [d if d > 0 else 0 for d in deltas]
                    losses = [-d if d < 0 else 0 for d in deltas]
                    period = rsi_len
                    avg_gain = sum(gains[:period]) / period
                    avg_loss = sum(losses[:period]) / period
                    for i in range(period, len(deltas)):
                        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                    if avg_loss == 0:
                        r["rsi7"] = 100.0
                    else:
                        rs = avg_gain / avg_loss
                        r["rsi7"] = round(100 - (100 / (1 + rs)), 1)

            conn.close()
            return rows

        risers = enrich(risers)
        fallers = enrich(fallers)

        return jsonify({
            "result": {
                "risers": risers,
                "fallers": fallers,
                "risers_index": risers_index,
                "fallers_index": fallers_index
            }
        })
    
    return jsonify({"error": "unknown tool"}), 404