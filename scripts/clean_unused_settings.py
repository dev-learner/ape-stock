# scripts/clean_unused_settings.py
# DESC: Remove unused Candidate Selection settings from app_settings
# RUN: Tool2

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

unused = [
    "cand_rank",
    "cand_require_faller",
    "cand_vs50_buy",
    "cand_vs200_buy",
    "cand_vs50_hold",
    "cand_vs50_sell",
]

print("Removing unused settings...")
for key in unused:
    cur.execute("DELETE FROM app_settings WHERE key = ?", (key,))
    print(f"  {key}: {cur.rowcount} row(s) deleted")

conn.commit()
conn.close()
print("Done.")