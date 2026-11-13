# holdings.py
import sqlite3
import time
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify
from data import fetch_quote
from db import get_db

UK = ZoneInfo("Europe/London")
bp = Blueprint("holdings", __name__)

def is_uk_trading_day(d):
    """Simple Mon-Fri check (bank holidays ignored for now)."""
    return d.weekday() < 5

def close_holding_internal(hid, exit_price, reason):
    """Close a holding and archive it. Used by both the route and background."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holdings WHERE id = ?", (hid,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return None

    proceeds = h["shares"] * exit_price
    pnl_net = proceeds - h["notional"]

    cur.execute("""
        SELECT day_offset, price, pnl_net FROM holdings_marks
        WHERE holding_id = ? ORDER BY day_offset
    """, (hid,))
    path = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        INSERT INTO holdings_history
        (symbol, entry_date, entry_price, exit_date, exit_price, notional, stamp_pct, shares,
         exit_reason, final_pnl_net, day_path, closed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        h["symbol"], h["entry_date"], h["entry_price"],
        datetime.now(UK).date().isoformat(), exit_price,
        h["notional"], h["stamp_pct"], h["shares"],
        reason, pnl_net, json.dumps(path),
        datetime.now(UK).isoformat()
    ))
    cur.execute("DELETE FROM holdings WHERE id = ?", (hid,))
    cur.execute("DELETE FROM holdings_marks WHERE holding_id = ?", (hid,))
    conn.commit()
    conn.close()
    return pnl_net

def refresh_live_holding_prices():
    """Update the highest day_offset mark with the live price. Retries briefly on database lock."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.id, h.symbol, h.shares, h.notional, h.entry_price,
               MAX(m.day_offset) as day_offset
        FROM holdings h
        JOIN holdings_marks m ON m.holding_id = h.id
        WHERE h.status = 'open'
        GROUP BY h.id
    """)
    holdings = cur.fetchall()
    conn.close()

    if not holdings:
        return

    today = datetime.now(UK).date().isoformat()
    for h in holdings:
        price = None
        try:
            q = fetch_quote(h["symbol"])
            price = q.get("price") if q else None
        except Exception:
            continue
        if price is None:
            continue

        pnl_net = (h["shares"] * price) - h["notional"] if h["shares"] else None
        day_offset = h["day_offset"] or 0

        for attempt in range(3):
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute("""
                    UPDATE holdings_marks
                    SET price = ?, pnl_net = ?, mark_date = ?
                    WHERE holding_id = ? AND day_offset = ?
                """, (price, pnl_net, today, h["id"], day_offset))
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < 2:
                    time.sleep(0.15)
                    continue
                try:
                    conn.close()
                except Exception:
                    pass
                break
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                break

@bp.route("/holdings/open", methods=["POST"])
def open_holding():
    data = request.get_json(silent=True) or {}
    symbol = data.get("symbol")
    price = data.get("price")
    print(f"[holdings/open] request for {symbol}", flush=True)
    if not symbol or not price:
        return jsonify({"error": "symbol and price required"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM holdings WHERE symbol = ? AND status = 'open'", (symbol,))
    existing = cur.fetchone()
    if existing:
        print(f"[holdings/open] REJECTED duplicate open for {symbol} (id={existing['id']})", flush=True)
        conn.close()
        return jsonify({"error": "already open", "symbol": symbol}), 409

    notional = float(data.get("notional") or 500)
    stamp_pct = float(data.get("stamp_pct") or 0.5)
    cost = notional * (stamp_pct / 100.0)
    invest = notional - cost
    shares = invest / float(price)

    now = datetime.now(UK).isoformat()
    entry_date = datetime.now(UK).date().isoformat()
    cur.execute("""
        INSERT INTO holdings (symbol, entry_date, entry_price, notional, stamp_pct, shares, status, created)
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
    """, (symbol, entry_date, price, notional, stamp_pct, shares, now))
    holding_id = cur.lastrowid

    cur.execute("""
        INSERT INTO holdings_marks (holding_id, day_offset, mark_date, price, pnl_net)
        VALUES (?, 0, ?, ?, 0)
    """, (holding_id, entry_date, price))
    conn.commit()
    conn.close()
    print(f"[holdings/open] created id={holding_id} for {symbol}", flush=True)
    return jsonify({"ok": True, "id": holding_id})

@bp.route("/holdings/list")
def list_holdings():
    refresh_live_holding_prices()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holdings WHERE status = 'open' ORDER BY entry_date DESC, id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    for h in rows:
        cur.execute("""
            SELECT day_offset, mark_date, price, pnl_net
            FROM holdings_marks
            WHERE holding_id = ?
            ORDER BY day_offset
        """, (h["id"],))
        h["marks"] = [dict(m) for m in cur.fetchall()]

        # Enrich with live quote + exchange
        cur.execute("""
            SELECT name, change, change_pct, volume
            FROM index_quotes WHERE symbol = ?
        """, (h["symbol"],))
        q = cur.fetchone()
        if q:
            h["name"] = q["name"]
            h["change"] = q["change"]
            h["change_pct"] = q["change_pct"]
            h["volume"] = q["volume"]
        else:
            h["name"] = h["symbol"]
            h["change"] = None
            h["change_pct"] = None
            h["volume"] = None

        cur.execute("""
            SELECT index_key FROM index_constituents
            WHERE symbol = ? ORDER BY CASE index_key WHEN '100' THEN 0 ELSE 1 END LIMIT 1
        """, (h["symbol"],))
        idx = cur.fetchone()
        h["exchange"] = idx["index_key"] if idx else ""

    conn.close()
    return jsonify(rows)

@bp.route("/holdings/close", methods=["POST"])
def close_holding():
    data = request.get_json(silent=True) or {}
    hid = data.get("id")
    reason = data.get("reason") or "manual"
    exit_price = data.get("exit_price")
    if not hid or exit_price is None:
        return jsonify({"error": "id and exit_price required"}), 400

    pnl = close_holding_internal(hid, float(exit_price), reason)
    if pnl is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"ok": True, "pnl_net": pnl})

@bp.route("/holdings/reset", methods=["POST"])
def reset_holdings():
    """Dev-only: clear all holdings, marks and history."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM holdings")
    cur.execute("DELETE FROM holdings_marks")
    cur.execute("DELETE FROM holdings_history")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})