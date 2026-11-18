# portfolio.py
from flask import Blueprint, request, jsonify
from db import get_db, get_setting
from datetime import datetime
from zoneinfo import ZoneInfo

bp = Blueprint("portfolio", __name__)
UK = ZoneInfo("Europe/London")

def _cash_balance(cur):
    """Return current cash balance from all transactions."""
    cur.execute("SELECT COALESCE(SUM(cash_impact), 0) FROM portfolio_transactions")
    return cur.fetchone()[0] or 0.0

def _total_deposited(cur):
    """Return total cash ever deposited (for P/L % calculation)."""
    cur.execute("SELECT COALESCE(SUM(cash_impact), 0) FROM portfolio_transactions WHERE type = 'DEPOSIT'")
    return cur.fetchone()[0] or 0.0

def _get_rank(cur, symbol, date_str):
    """Look up rank for symbol on a given date (YYYY-MM-DD)."""
    cur.execute("SELECT rank FROM daily_ranks WHERE symbol = ? AND date = ?", (symbol, date_str))
    row = cur.fetchone()
    return row[0] if row else None

@bp.route("/portfolio/summary")
def summary():
    """Return cash, total value, P/L % and current positions."""
    conn = get_db()
    cur = conn.cursor()
    cash = _cash_balance(cur)
    deposited = _total_deposited(cur)

    cur.execute("""
        SELECT p.symbol, p.quantity, p.avg_cost, q.price, q.name
        FROM portfolio_positions p
        LEFT JOIN index_quotes q ON q.symbol = p.symbol
        WHERE p.quantity > 0
    """)
    positions = []
    holdings_value = 0.0
    for r in cur.fetchall():
        # Live price is in pence
        last_pence = r["price"] or (r["avg_cost"] * 100)
        last_pounds = last_pence / 100.0
        value = r["quantity"] * last_pounds
        holdings_value += value

        # Total cost = (qty × avg price) + stamp paid on buys
        cur.execute("""
            SELECT COALESCE(SUM(costs), 0) FROM portfolio_transactions
            WHERE symbol = ? AND type = 'BUY'
        """, (r["symbol"],))
        total_stamp = cur.fetchone()[0] or 0.0
        total_cost = (r["quantity"] * r["avg_cost"]) + total_stamp

        pnl = value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost else 0.0

        # Most recent transaction timestamp (for optional use)
        cur.execute("""
            SELECT MAX(ts) FROM portfolio_transactions WHERE symbol = ?
        """, (r["symbol"],))
        last_ts = cur.fetchone()[0] or ""

        positions.append({
            "symbol": r["symbol"],
            "name": r["name"] or "",
            "quantity": r["quantity"],
            "avg_cost": r["avg_cost"],
            "total_cost": total_cost,
            "last_price_pence": last_pence,
            "value": value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "last_ts": last_ts
        })

    total_value = cash + holdings_value
    pl_pct = ((total_value - deposited) / deposited * 100) if deposited else 0.0

    conn.close()
    return jsonify({
        "cash": round(cash, 2),
        "value": round(total_value, 2),
        "pl_pct": round(pl_pct, 2),
        "positions": positions
    })

@bp.route("/portfolio/transactions")
def transactions():
    """Return transactions, newest first (by id). Optional filter: all|cash|shares."""
    filter_type = request.args.get("filter", "all")
    conn = get_db()
    cur = conn.cursor()
    if filter_type == "cash":
        cur.execute("""
            SELECT * FROM portfolio_transactions
            WHERE type IN ('DEPOSIT','WITHDRAW')
            ORDER BY id DESC
        """)
    elif filter_type == "shares":
        cur.execute("""
            SELECT * FROM portfolio_transactions
            WHERE type IN ('BUY','SELL')
            ORDER BY id DESC
        """)
    else:
        cur.execute("SELECT * FROM portfolio_transactions ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@bp.route("/portfolio/cash", methods=["POST"])
def cash_transaction():
    """Record a cash deposit or withdrawal."""
    data = request.get_json(silent=True) or {}
    amount = float(data.get("amount", 0))
    action = data.get("action")  # deposit or withdraw
    date_str = data.get("date") or datetime.now(UK).date().isoformat()

    if amount <= 0 or action not in ("deposit", "withdraw"):
        return jsonify({"error": "Invalid amount or action"}), 400

    conn = get_db()
    cur = conn.cursor()
    cash = _cash_balance(cur)
    if action == "withdraw" and amount > cash:
        conn.close()
        return jsonify({"error": "Insufficient cash"}), 400

    impact = amount if action == "deposit" else -amount
    typ = "DEPOSIT" if action == "deposit" else "WITHDRAW"
    ts = f"{date_str}T12:00:00"

    cur.execute("""
        INSERT INTO portfolio_transactions (ts, type, cash_impact, notes)
        VALUES (?, ?, ?, ?)
    """, (ts, typ, impact, data.get("notes", "")))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@bp.route("/portfolio/buy", methods=["POST"])
def buy():
    """Record a buy, update average-cost position, check cash."""
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or "").strip().upper()
    qty = float(data.get("quantity", 0))
    price = float(data.get("price", 0))
    date_str = data.get("date")
    if not symbol or qty <= 0 or price <= 0 or not date_str:
        return jsonify({"error": "Missing fields"}), 400

    stamp_pct = float(get_setting("stampPct", "0.5"))
    gross = qty * price
    costs = gross * (stamp_pct / 100.0)
    total = gross + costs

    conn = get_db()
    cur = conn.cursor()
    cash = _cash_balance(cur)
    if total > cash:
        conn.close()
        return jsonify({"error": "Insufficient cash"}), 400

    rank = _get_rank(cur, symbol, date_str)
    notes = f"Rank: {rank if rank is not None else 'n/a'}"
    ts = f"{date_str}T12:00:00"

    cur.execute("""
        INSERT INTO portfolio_transactions
        (ts, type, symbol, quantity, price, stamp_pct, costs, cash_impact, rank_at_date, notes)
        VALUES (?, 'BUY', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, symbol, qty, price, stamp_pct, costs, -total, rank, notes))

    # Update or create position (average cost, ex-stamp)
    cur.execute("SELECT quantity, avg_cost FROM portfolio_positions WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    if row:
        old_qty, old_avg = row["quantity"], row["avg_cost"]
        new_qty = old_qty + qty
        new_avg = (old_qty * old_avg + qty * price) / new_qty
        cur.execute("""
            UPDATE portfolio_positions
            SET quantity = ?, avg_cost = ?, updated = ?
            WHERE symbol = ?
        """, (new_qty, new_avg, ts, symbol))
    else:
        cur.execute("""
            INSERT INTO portfolio_positions (symbol, quantity, avg_cost, updated)
            VALUES (?, ?, ?, ?)
        """, (symbol, qty, price, ts))

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@bp.route("/portfolio/sell", methods=["POST"])
def sell():
    """Record a sell and reduce position (long only)."""
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or "").strip().upper()
    qty = float(data.get("quantity", 0))
    price = float(data.get("price", 0))
    date_str = data.get("date")
    if not symbol or qty <= 0 or price <= 0 or not date_str:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT quantity, avg_cost FROM portfolio_positions WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    if not row or row["quantity"] < qty:
        conn.close()
        return jsonify({"error": "Insufficient quantity"}), 400

    proceeds = qty * price
    rank = _get_rank(cur, symbol, date_str)
    notes = f"Rank: {rank if rank is not None else 'n/a'}"
    ts = f"{date_str}T12:00:00"

    cur.execute("""
        INSERT INTO portfolio_transactions
        (ts, type, symbol, quantity, price, cash_impact, rank_at_date, notes)
        VALUES (?, 'SELL', ?, ?, ?, ?, ?, ?)
    """, (ts, symbol, qty, price, proceeds, rank, notes))

    new_qty = row["quantity"] - qty
    if new_qty <= 0:
        cur.execute("DELETE FROM portfolio_positions WHERE symbol = ?", (symbol,))
    else:
        cur.execute("""
            UPDATE portfolio_positions SET quantity = ?, updated = ? WHERE symbol = ?
        """, (new_qty, ts, symbol))

    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@bp.route("/portfolio/reset", methods=["POST"])
def reset():
    """Development helper — wipe all portfolio data."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_transactions")
    cur.execute("DELETE FROM portfolio_positions")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})