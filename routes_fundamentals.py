# routes_fundamentals.py
# Fundamentals endpoint extracted from the original routes.py.

from flask import Blueprint, jsonify
from db import get_db

bp = Blueprint("fundamentals", __name__)

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