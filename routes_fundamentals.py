# routes_fundamentals.py
# Fundamentals endpoint.
# Modes:
#   base -> full universe ordered by base_rank (Rank # = base_rank)
#   fund -> full universe ordered by pure fund_rank (Rank # = fund_rank, dense 1-351)
# Always returns base_rank; "rank" holds the active ranking.

from flask import Blueprint, request, jsonify
from db import get_db

bp = Blueprint("fundamentals", __name__)

@bp.route("/fundamentals")
def fundamentals():
    """Return fundamentals snapshot for Tool 6.
    ?mode=base -> all names ordered by latest base_rank
    ?mode=fund -> all names ordered by pure fund_rank
    default    -> ordered by market cap (legacy)
    """
    mode = request.args.get("mode", "")
    conn = get_db()
    cur = conn.cursor()

    if mode == "base":
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
                f.current_ratio,
                s.base_rank,
                s.base_rank AS rank,
                q.price,
                q.change_pct
            FROM fundamentals f
            LEFT JOIN index_quotes q ON q.symbol = f.symbol
            LEFT JOIN stock_scores s ON s.symbol = f.symbol
                AND s.score_date = (SELECT MAX(score_date) FROM stock_scores)
            ORDER BY s.base_rank ASC NULLS LAST
        """)
    elif mode == "fund":
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
                f.current_ratio,
                s.base_rank,
                s.fund_rank AS rank,
                q.price,
                q.change_pct
            FROM fundamentals f
            LEFT JOIN index_quotes q ON q.symbol = f.symbol
            LEFT JOIN stock_scores s ON s.symbol = f.symbol
                AND s.score_date = (SELECT MAX(score_date) FROM stock_scores)
            ORDER BY s.fund_rank ASC NULLS LAST
        """)
    else:
        # Legacy market-cap order
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
                f.current_ratio,
                q.price,
                q.change_pct
            FROM fundamentals f
            LEFT JOIN index_quotes q ON q.symbol = f.symbol
            ORDER BY f.market_cap DESC NULLS LAST
        """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify({"rows": rows, "mode": mode or "default"})