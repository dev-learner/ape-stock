# portfolio.py
from flask import Blueprint, request, jsonify, Response
from db import get_db, get_setting
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import io
import json

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

def _get_name(cur, symbol):
    """Look up company name from index_quotes or external_constituents."""
    cur.execute("SELECT name FROM index_quotes WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    if row and row["name"]:
        return row["name"]
    cur.execute("SELECT name FROM external_constituents WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    return row["name"] if row else None

@bp.route("/portfolio/summary")
def summary():
    """Return cash, total value, P/L % and current positions."""
    conn = get_db()
    cur = conn.cursor()
    cash = _cash_balance(cur)
    deposited = _total_deposited(cur)

    cur.execute("""
        SELECT p.symbol, p.quantity, p.avg_cost,
               COALESCE(q.price, e.price) AS price,
               COALESCE(q.name, e.name, p.name) AS name
        FROM portfolio_positions p
        LEFT JOIN index_quotes q ON q.symbol = p.symbol
        LEFT JOIN external_constituents e ON e.symbol = p.symbol
        WHERE p.quantity > 0
    """)
    positions = []
    holdings_value = 0.0
    for r in cur.fetchall():
        last_pence = r["price"] or (r["avg_cost"] * 100)
        last_pounds = last_pence / 100.0
        value = r["quantity"] * last_pounds
        holdings_value += value

        cur.execute("""
            SELECT COALESCE(SUM(costs), 0) FROM portfolio_transactions
            WHERE symbol = ? AND type = 'BUY'
        """, (r["symbol"],))
        total_stamp = cur.fetchone()[0] or 0.0
        total_cost = (r["quantity"] * r["avg_cost"]) + total_stamp

        pnl = value - total_cost
        pnl_pct = (pnl / total_cost * 100) if total_cost else 0.0

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
    action = data.get("action")
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

    name = _get_name(cur, symbol)
    rank = _get_rank(cur, symbol, date_str)
    notes = f"Rank: {rank if rank is not None else 'n/a'}"
    ts = f"{date_str}T12:00:00"

    cur.execute("""
        INSERT INTO portfolio_transactions
        (ts, type, symbol, name, quantity, price, stamp_pct, costs, cash_impact, rank_at_date, notes)
        VALUES (?, 'BUY', ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ts, symbol, name, qty, price, stamp_pct, costs, -total, rank, notes))

    cur.execute("SELECT quantity, avg_cost FROM portfolio_positions WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    if row:
        old_qty, old_avg = row["quantity"], row["avg_cost"]
        new_qty = old_qty + qty
        new_avg = (old_qty * old_avg + qty * price) / new_qty
        cur.execute("""
            UPDATE portfolio_positions
            SET quantity = ?, avg_cost = ?, name = COALESCE(?, name), updated = ?
            WHERE symbol = ?
        """, (new_qty, new_avg, name, ts, symbol))
    else:
        cur.execute("""
            INSERT INTO portfolio_positions (symbol, name, quantity, avg_cost, updated)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, name, qty, price, ts))

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
    cur.execute("SELECT quantity FROM portfolio_positions WHERE symbol = ?", (symbol,))
    row = cur.fetchone()
    if not row or row["quantity"] < qty:
        conn.close()
        return jsonify({"error": "Insufficient quantity"}), 400

    name = _get_name(cur, symbol)
    proceeds = qty * price
    rank = _get_rank(cur, symbol, date_str)
    notes = f"Rank: {rank if rank is not None else 'n/a'}"
    ts = f"{date_str}T12:00:00"

    cur.execute("""
        INSERT INTO portfolio_transactions
        (ts, type, symbol, name, quantity, price, cash_impact, rank_at_date, notes)
        VALUES (?, 'SELL', ?, ?, ?, ?, ?, ?, ?)
    """, (ts, symbol, name, qty, price, proceeds, rank, notes))

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
    """Development helper — wipe all portfolio data and reset auto-increment."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_transactions")
    cur.execute("DELETE FROM portfolio_positions")
    cur.execute("DELETE FROM sqlite_sequence WHERE name = 'portfolio_transactions'")
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@bp.route("/portfolio/export")
def export():
    """Export all transactions as JSON or CSV."""
    fmt = request.args.get("format", "json").lower()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM portfolio_transactions ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    stamp = datetime.now(UK).strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"ape-stock_transactions_{stamp}"

    if fmt == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )
    else:
        return Response(
            json.dumps(rows, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )

@bp.route("/portfolio/import", methods=["POST"])
def import_data():
    """Wipe portfolio and import transactions from uploaded JSON or CSV."""
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    name = (f.filename or "").lower()
    raw = f.read().decode("utf-8")

    try:
        if name.endswith(".json"):
            rows = json.loads(raw)
        elif name.endswith(".csv"):
            reader = csv.DictReader(io.StringIO(raw))
            rows = list(reader)
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    except Exception as e:
        return jsonify({"error": f"Parse error: {e}"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM portfolio_transactions")
    cur.execute("DELETE FROM portfolio_positions")
    cur.execute("DELETE FROM sqlite_sequence WHERE name = 'portfolio_transactions'")

    for r in rows:
        cur.execute("""
            INSERT INTO portfolio_transactions
            (ts, type, symbol, name, quantity, price, stamp_pct, costs, cash_impact, rank_at_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r.get("ts"),
            r.get("type"),
            r.get("symbol") or None,
            r.get("name") or None,
            float(r["quantity"]) if r.get("quantity") else None,
            float(r["price"]) if r.get("price") else None,
            float(r["stamp_pct"]) if r.get("stamp_pct") else None,
            float(r["costs"]) if r.get("costs") else 0,
            float(r.get("cash_impact") or 0),
            int(r["rank_at_date"]) if r.get("rank_at_date") else None,
            r.get("notes")
        ))

    # Rebuild positions
    cur.execute("""
        SELECT symbol,
               SUM(CASE WHEN type='BUY' THEN quantity ELSE -quantity END) AS qty,
               SUM(CASE WHEN type='BUY' THEN quantity * price ELSE 0 END) AS cost_sum,
               SUM(CASE WHEN type='BUY' THEN quantity ELSE 0 END) AS buy_qty
        FROM portfolio_transactions
        WHERE type IN ('BUY','SELL') AND symbol IS NOT NULL
        GROUP BY symbol
        HAVING qty > 0
    """)
    for row in cur.fetchall():
        avg = row["cost_sum"] / row["buy_qty"] if row["buy_qty"] else 0
        cur.execute("""
            INSERT INTO portfolio_positions (symbol, quantity, avg_cost, updated)
            VALUES (?, ?, ?, datetime('now'))
        """, (row["symbol"], row["qty"], avg))

    conn.commit()
    conn.close()
    return jsonify({"ok": True, "imported": len(rows)})