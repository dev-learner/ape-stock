# routes_screener.py
# Screener endpoint extracted from the original routes.py.

from flask import Blueprint, request, jsonify
from db import get_db, get_setting

bp = Blueprint("screener", __name__)

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