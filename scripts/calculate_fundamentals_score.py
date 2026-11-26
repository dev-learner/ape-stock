# scripts/calculate_fundamentals_score.py
# NAME: Calculate Fundamentals Score
# DESC: Computes a simple 0-100 Fundamentals score from the fundamentals table.
# DETAIL: Uses pe_trailing, price_to_book and dividend_yield. Easy to extend later. Safe to re-run.
# ALLOW_DELETE: 1
# RUN: Tool2

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, pe_trailing, price_to_book, dividend_yield
        FROM fundamentals
        WHERE pe_trailing IS NOT NULL
    """)
    rows = cur.fetchall()

    def to_score(pe, pb, div_yield):
        score = 50.0  # neutral start
        # PE contribution (prefer roughly 8–25)
        if pe and 8 <= pe <= 25:
            score += 20
        elif pe and pe > 40:
            score -= 15
        # Price-to-book contribution (prefer lower)
        if pb and pb < 3:
            score += 15
        elif pb and pb > 8:
            score -= 10
        # Dividend presence
        if div_yield and div_yield > 0:
            score += 10
        return max(0, min(100, round(score, 1)))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for r in rows:
        score = to_score(r["pe_trailing"], r["price_to_book"], r["dividend_yield"])
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, fundamentals_score)
            VALUES (?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET fundamentals_score = excluded.fundamentals_score
        """, (r["symbol"], today, score))
        count += 1

    conn.commit()
    conn.close()
    print(f"Fundamentals scores written for {count} symbols.")

if __name__ == "__main__":
    main()