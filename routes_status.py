# routes_status.py
# Status, dashboard counts and schema viewer routes extracted from the original routes.py.

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify
from db import get_db, get_setting
from data import fetch_ftse

UK = ZoneInfo("Europe/London")
bp = Blueprint("status", __name__)

@bp.route("/status")
def status():
    """Return overall application status for the dashboard and status bar."""
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

@bp.route("/dashboard")
def dashboard():
    """Simple dashboard counts (legacy endpoint)."""
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