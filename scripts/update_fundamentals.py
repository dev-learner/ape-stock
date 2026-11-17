# scripts/update_fundamentals.py
# DESC: Update dedicated fundamentals table (and key fields in index_quotes) from yfinance
# RUN: Tool2

"""
Pulls fundamental data from yfinance and stores it in the dedicated
fundamentals table. Also keeps market_cap, sector, industry and avg_volume
in index_quotes so existing screener / rank code continues to work.

On first run it migrates any existing fundamental columns from index_quotes.
"""

import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=60)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ---------------------------------------------------------------------------
# One-time migration of existing data from index_quotes (if columns exist)
# ---------------------------------------------------------------------------
def column_exists(table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())

migrate_cols = [
    "sector", "industry", "market_cap", "avg_volume",
    "pe_trailing", "pe_forward", "dividend_yield",
    "shares_outstanding", "fifty_two_week_high", "fifty_two_week_low",
    "beta", "book_value", "price_to_book",
    "ex_dividend_date", "earnings_date"
]
existing = [c for c in migrate_cols if column_exists("index_quotes", c)]

if existing:
    print("Migrating existing fundamental data from index_quotes…")
    cols_sql = ", ".join(existing)
    cur.execute(f"""
        INSERT OR IGNORE INTO fundamentals (symbol, {cols_sql})
        SELECT symbol, {cols_sql}
        FROM index_quotes
        WHERE symbol IS NOT NULL
    """)
    conn.commit()
    print(f"Migrated {cur.rowcount} rows")

# ---------------------------------------------------------------------------
# Update from yfinance
# ---------------------------------------------------------------------------
def ts_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return None

cur.execute("SELECT symbol FROM index_constituents")
symbols = [r["symbol"] for r in cur.fetchall()]
print(f"Updating fundamentals for {len(symbols)} symbols…")

now = datetime.now(timezone.utc).isoformat()
updated = 0

for i, sym in enumerate(symbols, 1):
    try:
        info = yf.Ticker(sym).info or {}

        data = {
            "sector": info.get("sector") or info.get("sectorDisp"),
            "industry": info.get("industry") or info.get("industryDisp"),
            "market_cap": info.get("marketCap"),
            "avg_volume": info.get("averageDailyVolume3Month") or info.get("averageDailyVolume10Day"),
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "book_value": info.get("bookValue"),
            "price_to_book": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "free_cashflow": info.get("freeCashflow"),
            "current_ratio": info.get("currentRatio"),
            "ex_dividend_date": ts_to_date(info.get("exDividendDate")),
            "earnings_date": ts_to_date(info.get("earningsTimestamp") or info.get("earningsTimestampStart")),
            "updated": now,
        }

        # Upsert into fundamentals
        cols = list(data.keys())
        placeholders = ", ".join("?" * len(cols))
        updates = ", ".join(f"{c}=excluded.{c}" for c in cols)
        cur.execute(f"""
            INSERT INTO fundamentals (symbol, {", ".join(cols)})
            VALUES (?, {placeholders})
            ON CONFLICT(symbol) DO UPDATE SET {updates}
        """, [sym] + list(data.values()))

        # Keep critical fields in index_quotes for existing code
        cur.execute("""
            UPDATE index_quotes
            SET sector = COALESCE(?, sector),
                industry = COALESCE(?, industry),
                market_cap = COALESCE(?, market_cap),
                avg_volume = COALESCE(?, avg_volume)
            WHERE symbol = ?
        """, (
            data["sector"], data["industry"],
            data["market_cap"], data["avg_volume"],
            sym
        ))

        updated += 1
        if i % 25 == 0:
            print(f"  …{i}/{len(symbols)}", flush=True)
            conn.commit()
        time.sleep(0.3)
    except Exception as e:
        print(f"  {sym}: {e}")

# Record timestamp
cur.execute("""
    INSERT INTO app_settings (key, value)
    VALUES ('fundamentals_updated', ?)
    ON CONFLICT(key) DO UPDATE SET value = excluded.value
""", (now,))

conn.commit()
conn.close()
print(f"Done. Updated {updated} symbols.")