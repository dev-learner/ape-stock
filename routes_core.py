# routes_core.py
# Core routes and shared helpers extracted from the original routes.py.
# Contains the index page, tool placeholders, and the get_index_data helper.

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, render_template, request, jsonify
from db import get_db, get_setting, set_setting

UK = ZoneInfo("Europe/London")
bp = Blueprint("core", __name__)

def get_index_data(index_key, direction, limit=None, min_change=None, max_change=None):
    """Shared helper: return risers or fallers for a given index key.
    Used by Tool 8 and potentially future tools.
    """
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
    """Main application page."""
    return render_template("index.html")

@bp.route("/tool11")
def tool11_placeholder():
    """Placeholder endpoint for Tool 11 — Grok-It!"""
    return jsonify({
        "status": "ok",
        "message": "Tool 11 (Grok-It!) placeholder is live",
        "templates_dir": "grokit/"
    })

@bp.route("/tool12")
def tool12_placeholder():
    """Placeholder endpoint for Tool 12 — Screeners."""
    return jsonify({
        "status": "ok",
        "message": "Tool 12 (Screeners) placeholder is live",
        "next": "Recovery Screen with sparklines"
    })