# scripts/update_fundamentals.py
# NAME: Update Fundamentals
# DESC: Refreshes fundamental data for all FTSE constituents and appends a daily history snapshot.
# DETAIL: Pulls key fundamental fields from Yahoo Finance for every symbol in index_constituents and upserts them into the fundamentals table. Also writes a dated row into fundamentals_history so changes can be tracked over time. Automatically run by the application when the data is stale. Safe to run manually. Does not delete existing history.
# ALLOW_DELETE: 0
# RUN: Tool2

"""
Update Fundamentals
-------------------
Fetches the latest fundamental snapshot for every FTSE 100 & FTSE 250
constituent via yfinance and stores it in two places:

1. fundamentals          – current snapshot (one row per symbol)
2. fundamentals_history  – daily history (one row per symbol per day)

Fields collected include sector, industry, market cap, PE ratios,
dividend yield, margins, ROE, free cash flow, etc.

The script is called automatically from app.py when the stored timestamp
is older than the configured threshold. It can also be run manually from
Tool 2.
"""

import sqlite3
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
import warnings

warnings.filterwarnings("ignore")

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"
UK = ZoneInfo("Europe/London")

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure history table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals_history (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            market_cap INTEGER,
            avg_volume INTEGER,
            pe_trailing REAL,
            pe_forward REAL,
            dividend_yield REAL,
            shares_outstanding INTEGER,
            fifty_two_week_high REAL,
            fifty_two_week_low REAL,
            beta REAL,
            book_value REAL,
            price_to_book REAL,
            roe REAL,
            profit_margin REAL,
            operating_margin REAL,
            revenue_growth REAL,
            free_cashflow REAL,
            current_ratio REAL,
            ex_dividend_date TEXT,
            earnings_date TEXT,
            PRIMARY KEY (symbol, date)
        )
    """)
    conn.commit()

    cur.execute("SELECT symbol FROM index_constituents")
    symbols = [r[0] for r in cur.fetchall()]
    print(f"Updating fundamentals for {len(symbols)} symbols...")

    today = datetime.now(UK).date().isoformat()
    updated = 0

    for i, symbol in enumerate(symbols, 1):
        try:
            info = yf.Ticker(symbol).info or {}

            def g(key, default=None):
                v = info.get(key)
                return v if v is not None else default

            data = {
                "sector": g("sector"),
                "industry": g("industry"),
                "market_cap": g("marketCap"),
                "avg_volume": g("averageVolume"),
                "pe_trailing": g("trailingPE"),
                "pe_forward": g("forwardPE"),
                "dividend_yield": g("dividendYield"),
                "shares_outstanding": g("sharesOutstanding"),
                "fifty_two_week_high": g("fiftyTwoWeekHigh"),
                "fifty_two_week_low": g("fiftyTwoWeekLow"),
                "beta": g("beta"),
                "book_value": g("bookValue"),
                "price_to_book": g("priceToBook"),
                "roe": g("returnOnEquity"),
                "profit_margin": g("profitMargins"),
                "operating_margin": g("operatingMargins"),
                "revenue_growth": g("revenueGrowth"),
                "free_cashflow": g("freeCashflow"),
                "current_ratio": g("currentRatio"),
                "ex_dividend_date": g("exDividendDate"),
                "earnings_date": None,
            }

            # Upsert current snapshot
            cur.execute("""
                INSERT INTO fundamentals (
                    symbol, sector, industry, market_cap, avg_volume,
                    pe_trailing, pe_forward, dividend_yield, shares_outstanding,
                    fifty_two_week_high, fifty_two_week_low, beta, book_value,
                    price_to_book, roe, profit_margin, operating_margin,
                    revenue_growth, free_cashflow, current_ratio,
                    ex_dividend_date, earnings_date, updated
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                ON CONFLICT(symbol) DO UPDATE SET
                    sector=excluded.sector,
                    industry=excluded.industry,
                    market_cap=excluded.market_cap,
                    avg_volume=excluded.avg_volume,
                    pe_trailing=excluded.pe_trailing,
                    pe_forward=excluded.pe_forward,
                    dividend_yield=excluded.dividend_yield,
                    shares_outstanding=excluded.shares_outstanding,
                    fifty_two_week_high=excluded.fifty_two_week_high,
                    fifty_two_week_low=excluded.fifty_two_week_low,
                    beta=excluded.beta,
                    book_value=excluded.book_value,
                    price_to_book=excluded.price_to_book,
                    roe=excluded.roe,
                    profit_margin=excluded.profit_margin,
                    operating_margin=excluded.operating_margin,
                    revenue_growth=excluded.revenue_growth,
                    free_cashflow=excluded.free_cashflow,
                    current_ratio=excluded.current_ratio,
                    ex_dividend_date=excluded.ex_dividend_date,
                    earnings_date=excluded.earnings_date,
                    updated=excluded.updated
            """, (
                symbol,
                data["sector"], data["industry"], data["market_cap"], data["avg_volume"],
                data["pe_trailing"], data["pe_forward"], data["dividend_yield"], data["shares_outstanding"],
                data["fifty_two_week_high"], data["fifty_two_week_low"], data["beta"], data["book_value"],
                data["price_to_book"], data["roe"], data["profit_margin"], data["operating_margin"],
                data["revenue_growth"], data["free_cashflow"], data["current_ratio"],
                data["ex_dividend_date"], data["earnings_date"],
                datetime.now(UK).isoformat()
            ))

            # Append to daily history
            cur.execute("""
                INSERT OR REPLACE INTO fundamentals_history (
                    symbol, date, sector, industry, market_cap, avg_volume,
                    pe_trailing, pe_forward, dividend_yield, shares_outstanding,
                    fifty_two_week_high, fifty_two_week_low, beta, book_value,
                    price_to_book, roe, profit_margin, operating_margin,
                    revenue_growth, free_cashflow, current_ratio,
                    ex_dividend_date, earnings_date
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
            """, (
                symbol, today,
                data["sector"], data["industry"], data["market_cap"], data["avg_volume"],
                data["pe_trailing"], data["pe_forward"], data["dividend_yield"], data["shares_outstanding"],
                data["fifty_two_week_high"], data["fifty_two_week_low"], data["beta"], data["book_value"],
                data["price_to_book"], data["roe"], data["profit_margin"], data["operating_margin"],
                data["revenue_growth"], data["free_cashflow"], data["current_ratio"],
                data["ex_dividend_date"], data["earnings_date"]
            ))

            updated += 1
            if i % 25 == 0:
                print(f"  …{i}/{len(symbols)}", flush=True)
                conn.commit()
            time.sleep(0.25)

        except Exception as e:
            print(f"  {symbol}: {e}")

    # Record timestamp
    cur.execute("""
        INSERT INTO app_settings (key, value) VALUES ('fundamentals_updated', ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (datetime.now(UK).isoformat(),))

    conn.commit()
    conn.close()
    print(f"Done. Updated {updated} symbols. History written for {today}.")

if __name__ == "__main__":
    main()