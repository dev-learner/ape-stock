# scripts/probe_yfinance_fundamentals.py
# DESC: Probe yfinance fundamental coverage and sample values for FTSE names
# RUN: Tool2

"""
Samples FTSE constituents and queries yfinance for key fundamental fields.
Reports:
- Coverage (% of symbols that return a non-null value) for each field
- A few sample values
- Any obvious data-quality issues

Designed to be run once (or occasionally) so we know what is actually
available before integrating valuation / quality columns into the Screener.
"""

import sqlite3
import time
from pathlib import Path
from collections import defaultdict
import yfinance as yf

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SAMPLE_SIZE = 40          # number of symbols to test (keeps runtime reasonable)
SLEEP_BETWEEN = 0.4       # seconds between requests to be polite to Yahoo
DB_NAME = "ape_stock.db"

# Fields we care about (yfinance info key -> friendly name)
FIELDS = {
    "trailingPE":           "Trailing PE",
    "forwardPE":            "Forward PE",
    "priceToBook":          "Price / Book",
    "dividendYield":        "Dividend Yield",
    "returnOnEquity":       "ROE",
    "profitMargins":        "Profit Margin",
    "operatingMargins":     "Operating Margin",
    "grossMargins":         "Gross Margin",
    "ebitdaMargins":        "EBITDA Margin",
    "debtToEquity":         "Debt / Equity",
    "currentRatio":         "Current Ratio",
    "quickRatio":           "Quick Ratio",
    "earningsGrowth":       "Earnings Growth",
    "revenueGrowth":        "Revenue Growth",
    "freeCashflow":         "Free Cash Flow",
    "operatingCashflow":    "Operating Cash Flow",
    "enterpriseToEbitda":   "EV / EBITDA",
    "beta":                 "Beta",
    "marketCap":            "Market Cap",
    "averageVolume":        "Avg Volume",
}

# ---------------------------------------------------------------------------
# Load sample of symbols
# ---------------------------------------------------------------------------
db_path = Path(__file__).parent.parent / DB_NAME
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT symbol
    FROM index_constituents
    ORDER BY RANDOM()
    LIMIT ?
""", (SAMPLE_SIZE,))
symbols = [r["symbol"] for r in cur.fetchall()]
conn.close()

print(f"Probing {len(symbols)} random FTSE symbols via yfinance...\n")

# ---------------------------------------------------------------------------
# Query yfinance
# ---------------------------------------------------------------------------
results = defaultdict(list)          # field -> list of (symbol, value)
coverage = defaultdict(int)          # field -> count of non-null
errors = []

for i, symbol in enumerate(symbols, 1):
    print(f"[{i:>2}/{len(symbols)}] {symbol}", end=" ", flush=True)
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        if not info:
            print("empty info")
            errors.append(symbol)
            time.sleep(SLEEP_BETWEEN)
            continue

        for key in FIELDS:
            val = info.get(key)
            if val is not None and val != "N/A" and val != "":
                # yfinance sometimes returns very large or tiny numbers; keep as-is for now
                results[key].append((symbol, val))
                coverage[key] += 1
        print("ok")
    except Exception as e:
        print(f"error: {e}")
        errors.append(symbol)
    time.sleep(SLEEP_BETWEEN)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"Coverage report ({len(symbols)} symbols tested)")
print("=" * 70)
print(f"{'Field':<22} {'Coverage':>10} {'%':>7}  Sample values")
print("-" * 70)

for key, label in FIELDS.items():
    count = coverage[key]
    pct = (count / len(symbols) * 100) if symbols else 0
    samples = results[key][:3]
    sample_str = ", ".join(f"{s}={v}" for s, v in samples) if samples else "—"
    print(f"{label:<22} {count:>10} {pct:>6.1f}%  {sample_str}")

print("\n" + "=" * 70)
print(f"Errors / empty responses: {len(errors)}")
if errors:
    print("Symbols:", ", ".join(errors[:15]) + ("..." if len(errors) > 15 else ""))

print("\nDone.")