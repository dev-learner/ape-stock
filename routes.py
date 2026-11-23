# routes.py
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, jsonify
from db import get_db, get_setting, set_setting
from data import fetch_quotes, fetch_news, fetch_ftse, refresh_constituents

UK = ZoneInfo("Europe/London")
bp = Blueprint("main", __name__)

def get_index_data(index_key, direction, limit=None, min_change=None, max_change=None):
    conn = get_db()
    cur = conn.cursor()
    if index_key == "ALL":
        cur.execute("SELECT symbol FROM index_constituents")
    else:
        cur.execute("SELECT symbol FROM index_constituents WHERE index_key = ?", (index_key,))
    symbols = [row[0] for row in cur.fetchall()]
    if not symbols:
        conn.close()
        return []

    placeholders = ",".join("?" * len(symbols))
    order = "DESC" if direction == "gainers" else "ASC"

    where_extra = ""
    params = symbols[:]
    if min_change is not None and direction == "gainers":
        where_extra += " AND change_pct >= ?"
        params.append(min_change)
    if max_change is not None and direction == "losers":
        where_extra += " AND change_pct <= ?"
        params.append(max_change)

    limit_sql = ""
    if limit is not None:
        limit_sql = "LIMIT ?"
        params.append(limit)

    cur.execute(f"""
        SELECT * FROM index_quotes
        WHERE symbol IN ({placeholders})
          AND change_pct IS NOT NULL
          {where_extra}
        ORDER BY change_pct {order}
        {limit_sql}
    """, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/tool11")
def tool11_placeholder():
    """Placeholder endpoint for Tool 11 — Grok-It!"""
    return jsonify({
        "status": "ok",
        "message": "Tool 11 (Grok-It!) placeholder is live",
        "templates_dir": "grokit/"
    })

@bp.route("/settings")
def settings():
    return render_template("settings.html")

@bp.route("/settings/save", methods=["POST"])
def settings_save():
    data = request.get_json(silent=True) or {}

    # Tracker close target
    target = data.get("tracker_close_target")
    if target is not None:
        try:
            val = float(target)
            val = max(1, min(10, val))
            set_setting("tracker_close_target", val)
        except (TypeError, ValueError):
            pass

    # Valuation toggle
    if "use_valuation" in data:
        set_setting("use_valuation", "1" if str(data["use_valuation"]) in ("1", "true", "True") else "0")

    # All other settings stored as strings
    for key in (
        "listLimit", "riserPct", "fallerPct", "hitThreshold", "notional", "stampPct",
        "rsiOversold", "rsiOverbought", "rsiLength",
        "rank_window", "rank_presence", "rank_cutoff",
        "pe_min", "pe_max", "pb_max", "require_dividend",
        "cand_rank_max", "cand_pe_min", "cand_pe_max", "cand_pb_max", "cand_require_div"
    ):
        if key in data and data[key] is not None:
            set_setting(key, str(data[key]))

    return jsonify({"ok": True})


@bp.route("/settings/get")
def settings_get():
    return jsonify({
        "tracker_close_target": get_setting("tracker_close_target", "3"),
        "listLimit": get_setting("listLimit", "25"),
        "riserPct": get_setting("riserPct", "3"),
        "fallerPct": get_setting("fallerPct", "3"),
        "hitThreshold": get_setting("hitThreshold", "50"),
        "notional": get_setting("notional", "500"),
        "stampPct": get_setting("stampPct", "0.5"),
        "rank_window": get_setting("rank_window", "35"),
        "rank_presence": get_setting("rank_presence", "50"),
        "rank_cutoff": get_setting("rank_cutoff", "12"),
        "pe_min": get_setting("pe_min", "5"),
        "pe_max": get_setting("pe_max", "40"),
        "pb_max": get_setting("pb_max", "4"),
        "require_dividend": get_setting("require_dividend", "0"),
        "use_valuation": get_setting("use_valuation", "0"),
        "rsiOversold": get_setting("rsiOversold", "30"),
        "rsiOverbought": get_setting("rsiOverbought", "70"),
        "rsiLength": get_setting("rsiLength", "7"),
        "cand_rank_max": get_setting("cand_rank_max", "12"),
        "cand_pe_min": get_setting("cand_pe_min", "5"),
        "cand_pe_max": get_setting("cand_pe_max", "40"),
        "cand_pb_max": get_setting("cand_pb_max", "4"),
        "cand_require_div": get_setting("cand_require_div", "0"),        
    })

@bp.route("/status")
def status():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    UK = ZoneInfo("Europe/London")

    conn = get_db()
    cur = conn.cursor()

    # Constituents
    cur.execute("SELECT COUNT(DISTINCT symbol) FROM index_constituents")
    constituents = cur.fetchone()[0] or 0

    # Screener metrics timestamp
    cur.execute("SELECT value FROM app_settings WHERE key = 'screener_metrics_updated'")
    row = cur.fetchone()
    metrics_updated = row[0] if row else None

    # Daily closes last date
    cur.execute("SELECT MAX(date) FROM daily_closes")
    row = cur.fetchone()
    daily_last = row[0] if row else None

    # Riser / Faller counts (respecting listLimit setting)
    raw_limit = get_setting("listLimit", "25")
    if str(raw_limit).lower() == "all":
        limit_sql = ""
        limit_params = []
    else:
        try:
            n = max(1, int(raw_limit))
        except (TypeError, ValueError):
            n = 25
        limit_sql = "LIMIT ?"
        limit_params = [n]

    cur.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT symbol FROM index_quotes
            WHERE change_pct IS NOT NULL AND change_pct > 0
            ORDER BY change_pct DESC
            {limit_sql}
        )
    """, limit_params)
    risers_count = cur.fetchone()[0] or 0

    cur.execute(f"""
        SELECT COUNT(*) FROM (
            SELECT symbol FROM index_quotes
            WHERE change_pct IS NOT NULL AND change_pct < 0
            ORDER BY change_pct ASC
            {limit_sql}
        )
    """, limit_params)
    fallers_count = cur.fetchone()[0] or 0

    conn.close()

    # Keep your existing FTSE values (replace the numbers with your live calculation if it differs)
    now = datetime.now(UK)
    ftse_data = fetch_ftse()

    last_update_iso = now.isoformat()

    return jsonify({
        "ftse": ftse_data,
        "last_update": last_update_iso,
        "last_background_update": last_update_iso,
        "symbols": constituents,
        "constituents": constituents,
        "screener_metrics_updated": metrics_updated,
        "daily_closes_last": daily_last,
        "risers": risers_count,
        "fallers": fallers_count
    })

@bp.route("/tool/<int:tool_id>", methods=["POST"])
def run_tool(tool_id):
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

@bp.route("/quotes", methods=["POST"])
def quotes():
    symbols = request.json.get("symbols", []) if request.is_json else []
    symbols = [s for s in symbols if isinstance(s, str) and s.strip()]
    return jsonify(fetch_quotes(symbols))

@bp.route("/sparkline/<symbol>")
def sparkline(symbol):
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

@bp.route("/schema")
def schema():
    """Return full database schema plus the most recent row values for each table."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    result = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        columns = [{"name": r[1], "type": r[2]} for r in cur.fetchall()]
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]

        # Grab the newest row (best-effort: prefer a timestamp-like column if present)
        latest = {}
        try:
            # Prefer common timestamp columns for ordering
            order_col = None
            for candidate in ("updated", "created", "date", "ts", "timestamp", "id"):
                if any(c["name"] == candidate for c in columns):
                    order_col = candidate
                    break
            if order_col:
                cur.execute(f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT 1")
            else:
                cur.execute(f"SELECT * FROM {table} LIMIT 1")
            row = cur.fetchone()
            if row:
                latest = dict(row)
        except Exception:
            latest = {}

        result.append({
            "table": table,
            "columns": columns,
            "rows": count,
            "latest": latest
        })
    conn.close()

    db_path = "ape_stock.db"
    size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    size_mb = round(size_bytes / (1024 * 1024), 2)
    return jsonify({"tables": result, "db_size_mb": size_mb, "db_size_bytes": size_bytes})

@bp.route("/screener")
def screener():
    """Return Screener names with today's rank.
    ?mode=full  -> all ranked symbols (including those failing current filters)
    default     -> only current safe-bet names
    """
    mode = request.args.get("mode", "optimal")
    conn = get_db()
    cur = conn.cursor()

    # Valuation filter settings
    use_valuation = get_setting("use_valuation", "0") == "1"
    try:
        pe_min = float(get_setting("pe_min", "5"))
    except (TypeError, ValueError):
        pe_min = 5.0
    try:
        pe_max = float(get_setting("pe_max", "40"))
    except (TypeError, ValueError):
        pe_max = 40.0
    try:
        pb_max = float(get_setting("pb_max", "4"))
    except (TypeError, ValueError):
        pb_max = 4.0
    require_div = get_setting("require_dividend", "1") == "1"

    cur.execute("SELECT MAX(date) FROM daily_ranks")
    row = cur.fetchone()
    rank_date = row[0] if row and row[0] else None

    valuation_sql = ""
    valuation_params = []
    if use_valuation:
        valuation_sql = """
            AND (f.pe_trailing IS NULL OR f.pe_trailing BETWEEN ? AND ?)
            AND (f.price_to_book IS NULL OR f.price_to_book < ?)
        """
        valuation_params = [pe_min, pe_max, pb_max]
        if require_div:
            valuation_sql += " AND (f.dividend_yield IS NULL OR f.dividend_yield > 0)"

    if mode == "full" and rank_date:
        cur.execute("""
            SELECT q.symbol, q.name, q.sector, q.price, q.change_pct,
                   q.ret_3m, q.ret_6m, q.dist_52w_high,
                   q.above_50ma, q.pct_from_50ma,
                   q.above_200ma, q.pct_from_200ma,
                   q.vol_20d, q.sector_rel_1d, q.sector_rel_5d,
                   q.market_cap, q.avg_volume,
                   r.rank
            FROM daily_ranks r
            LEFT JOIN index_quotes q ON q.symbol = r.symbol
            WHERE r.date = ?
            ORDER BY r.rank ASC
        """, (rank_date,))
    elif rank_date:
        sql = f"""
            SELECT q.symbol, q.name, q.sector, q.price, q.change_pct,
                   q.ret_3m, q.ret_6m, q.dist_52w_high,
                   q.above_50ma, q.pct_from_50ma,
                   q.above_200ma, q.pct_from_200ma,
                   q.vol_20d, q.sector_rel_1d, q.sector_rel_5d,
                   q.market_cap, q.avg_volume,
                   r.rank
            FROM index_quotes q
            LEFT JOIN daily_ranks r
                   ON r.symbol = q.symbol AND r.date = ?
            LEFT JOIN fundamentals f ON f.symbol = q.symbol
            WHERE q.above_50ma = 1
              AND q.above_200ma = 1
              AND (q.ret_3m IS NULL OR q.ret_3m > -15)
              AND (q.market_cap IS NULL OR q.market_cap > 2000000000)
              AND q.price IS NOT NULL
              {valuation_sql}
            ORDER BY r.rank ASC NULLS LAST, q.ret_3m DESC
            LIMIT 100
        """
        cur.execute(sql, [rank_date] + valuation_params)
    else:
        sql = f"""
            SELECT q.symbol, q.name, q.sector, q.price, q.change_pct,
                   q.ret_3m, q.ret_6m, q.dist_52w_high,
                   q.above_50ma, q.pct_from_50ma,
                   q.above_200ma, q.pct_from_200ma,
                   q.vol_20d, q.sector_rel_1d, q.sector_rel_5d,
                   q.market_cap, q.avg_volume,
                   NULL AS rank
            FROM index_quotes q
            LEFT JOIN fundamentals f ON f.symbol = q.symbol
            WHERE q.above_50ma = 1
              AND q.above_200ma = 1
              AND (q.ret_3m IS NULL OR q.ret_3m > -15)
              AND (q.market_cap IS NULL OR q.market_cap > 2000000000)
              AND q.price IS NOT NULL
              {valuation_sql}
            ORDER BY q.ret_3m DESC
            LIMIT 100
        """
        cur.execute(sql, valuation_params)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"rows": rows, "rank_date": rank_date, "mode": mode})

@bp.route("/dashboard")
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM index_quotes WHERE change_pct >= 2")
    risers = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM index_quotes WHERE change_pct <= -2")
    fallers = cur.fetchone()[0] or 0
    last = "—"
    for col in ("updated", "last_updated", "timestamp", "ts", "last_update"):
        try:
            cur.execute(f"SELECT MAX({col}) FROM index_quotes")
            val = cur.fetchone()[0]
            if val:
                last = val
                break
        except Exception:
            continue
    conn.close()
    return jsonify({
        "risers_count": risers,
        "fallers_count": fallers,
        "last_update": last
    })

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

@bp.route("/fundamentals")
def fundamentals():
    """Return latest fundamentals snapshot for Tool 6."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            f.symbol,
            q.name,
            f.sector,
            f.market_cap,
            f.pe_trailing,
            f.pe_forward,
            f.price_to_book,
            f.dividend_yield,
            f.roe,
            f.profit_margin,
            f.revenue_growth,
            f.beta,
            f.current_ratio
        FROM fundamentals f
        LEFT JOIN index_quotes q ON q.symbol = f.symbol
        ORDER BY f.market_cap DESC NULLS LAST
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"rows": rows})

@bp.route("/admin/bugs", methods=["GET", "POST"])
def bugs():
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        data = request.get_json() or {}
        cur.execute("""
            INSERT INTO bugettes (description, expected, tool, created)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("description", "").strip(),
            data.get("expected", "").strip(),
            data.get("tool", "").strip(),
            datetime.now(UK).isoformat()
        ))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    cur.execute("SELECT * FROM bugettes WHERE status = 'open' ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)


@bp.route("/admin/bugs/prompt")
def bug_prompt():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bugettes WHERE status = 'open' ORDER BY id")
    bugs = cur.fetchall()
    conn.close()

    if not bugs:
        prompt = "No open bugs."
    else:
        prompt = "The following errors have been reported:\n\n"
        for b in bugs:
            prompt += f"- Tool: {b['tool'] or '—'}\n"
            prompt += f"  Description: {b['description']}\n"
            prompt += f"  Expected: {b['expected'] or '—'}\n\n"
        prompt += """1 - Use the latest files from ape-stock's repo. (https://github.com/dev-learner/ape-stock)
2 - IMPORTANT - For any file that is edited:
a) - If the edit is 'minor' return the complete function.
b) - If the edit is more than 'minor' return the complete file.
3 - Confirm your understanding of the 'issues'
4 - Any initial questions before coding- Please ask."""

    return jsonify({"prompt": prompt})


@bp.route("/admin/bugs/signoff", methods=["POST"])
def bug_signoff():
    data = request.get_json() or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"ok": True})

    conn = get_db()
    cur = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    cur.execute(f"""
        UPDATE bugettes
        SET status = 'closed'
        WHERE id IN ({placeholders})
    """, ids)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

