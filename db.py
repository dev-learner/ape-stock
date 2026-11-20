# db.py
import sqlite3
from pathlib import Path
import datetime
from datetime import datetime, timezone

DB_PATH = "ape_stock.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS index_constituents (
            index_key TEXT,
            symbol TEXT,
            PRIMARY KEY (index_key, symbol)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS index_quotes (
            symbol TEXT PRIMARY KEY,
            price REAL,
            change REAL,
            change_pct REAL,
            volume INTEGER,
            avg_volume INTEGER,
            name TEXT,
            last_update TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            added TEXT,
            added_price REAL,
            news_count INTEGER DEFAULT 0,
            news_snippets TEXT,
            news_checked_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots_5min (
            symbol TEXT,
            ts TEXT,
            price REAL,
            change_pct REAL,
            volume INTEGER,
            avg_volume INTEGER,
            PRIMARY KEY (symbol, ts)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_closes (
            symbol TEXT,
            date TEXT,
            close REAL,
            PRIMARY KEY (symbol, date)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ftse_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            previous_close REAL,
            previous_was_up INTEGER
        )
    """)
    cur.execute("INSERT OR IGNORE INTO ftse_state (id) VALUES (1)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS constituents_meta (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            fingerprint TEXT,
            updated TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO constituents_meta (id) VALUES (1)")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            notional REAL NOT NULL,
            stamp_pct REAL NOT NULL,
            shares REAL NOT NULL,
            status TEXT DEFAULT 'open',
            created TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS holdings_marks (
            holding_id INTEGER,
            day_offset INTEGER,
            mark_date TEXT,
            price REAL,
            pnl_net REAL,
            PRIMARY KEY (holding_id, day_offset)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS holdings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            entry_date TEXT,
            entry_price REAL,
            exit_date TEXT,
            exit_price REAL,
            notional REAL,
            stamp_pct REAL,
            shares REAL,
            exit_reason TEXT,
            final_pnl_net REAL,
            day_path TEXT,
            closed_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('tracker_close_target', '3')")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_ranks (
            symbol TEXT,
            date TEXT,
            rank INTEGER,
            score REAL,
            persistence_days INTEGER,
            PRIMARY KEY (symbol, date)
        )
    """)

    # Dedicated fundamentals table (one row per symbol)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            symbol TEXT PRIMARY KEY,
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
            updated TEXT
        )
    """)
    
    # Portfolio
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            type TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            quantity REAL,
            price REAL,
            stamp_pct REAL,
            costs REAL DEFAULT 0,
            cash_impact REAL NOT NULL,
            rank_at_date INTEGER,
            notes TEXT,
            created TEXT DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_positions (
            symbol TEXT PRIMARY KEY,
            quantity REAL NOT NULL,
            avg_cost REAL NOT NULL,
            updated TEXT
        )
    """)

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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS external_constituents (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            market TEXT,
            price REAL,
            updated TEXT
        )
    """)    

    conn.commit()
    conn.close()

def get_ftse_state():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT previous_close, previous_was_up FROM ftse_state WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {"previous_close": None, "previous_was_up": None}

def save_ftse_state(previous_close, previous_was_up):
    conn = get_db()
    cur = conn.cursor()
    flag = None if previous_was_up is None else (1 if previous_was_up else 0)
    cur.execute("""
        UPDATE ftse_state SET previous_close = ?, previous_was_up = ? WHERE id = 1
    """, (previous_close, flag))
    conn.commit()
    conn.close()

def get_constituents_fingerprint():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT fingerprint FROM constituents_meta WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return row["fingerprint"] if row else None

def save_constituents_fingerprint(fp):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE constituents_meta
        SET fingerprint = ?, updated = ?
        WHERE id = 1
    """, (fp, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO app_settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()