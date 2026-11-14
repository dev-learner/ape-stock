# background.py
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import yfinance as yf
from db import get_db, get_setting
from data import fetch_quote
import warnings
warnings.filterwarnings("ignore", category=Warning)

UK = ZoneInfo("Europe/London")

def write_snapshot(q):
    if not q or q.get("price") is None:
        return
    minute = datetime.now(UK).minute
    rounded = minute - (minute % 5)
    ts = datetime.now(UK).replace(minute=rounded, second=0, microsecond=0).isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO snapshots_5min
        (symbol, ts, price, change_pct, volume, avg_volume)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (q["symbol"], ts, q["price"], q["change_pct"], q["volume"], q["avg_volume"]))
    conn.commit()
    conn.close()

def collapse_old_snapshots():
    cutoff = (datetime.now(UK) - timedelta(days=90)).date().isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, date(ts) as d, price
        FROM snapshots_5min
        WHERE date(ts) < ?
        ORDER BY symbol, ts
    """, (cutoff,))
    rows = cur.fetchall()
    daily = {}
    for r in rows:
        daily[(r["symbol"], r["d"])] = r["price"]
    for (sym, d), close in daily.items():
        cur.execute("""
            INSERT OR REPLACE INTO daily_closes (symbol, date, close)
            VALUES (?, ?, ?)
        """, (sym, d, close))
    cur.execute("DELETE FROM snapshots_5min WHERE date(ts) < ?", (cutoff,))
    conn.commit()
    conn.close()

def catchup_daily_closes():
    """Fill any missing daily closes. Skips when the market is closed and data is already current."""
    now = datetime.now(UK)
    is_weekday = now.weekday() < 5
    market_open = is_weekday and 8 <= now.hour < 17

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT MAX(date) FROM daily_closes")
    row = cur.fetchone()
    last_date_str = row[0] if row and row[0] else None
    conn.close()

    def last_trading_day(d):
        """Return the most recent Mon-Fri on or before d."""
        while d.weekday() >= 5:          # Sat/Sun
            d -= timedelta(days=1)
        return d

    today = now.date()
    expected = last_trading_day(today if market_open or now.hour >= 17 else today - timedelta(days=1))

    if last_date_str:
        last_dt = datetime.fromisoformat(last_date_str).date()
        if not market_open and last_dt >= expected:
            print(f"Catch-up: market closed, daily_closes already current (last={last_date_str}) — skipping")
            return
        print(f"Catch-up: daily_closes last date = {last_date_str}, filling gaps…")
    else:
        print("Catch-up: no daily_closes yet — running full fill")

    # --- fill logic ---
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM index_constituents")
    symbols = [r[0] for r in cur.fetchall()]
    conn.close()

    if not symbols:
        print("Catch-up: no constituents found")
        return

    end = now.date()
    if last_date_str:
        start = datetime.fromisoformat(last_date_str).date() + timedelta(days=1)
    else:
        start = end - timedelta(days=30)

    if start > end:
        print("Catch-up: nothing to fill")
        return

    print(f"Catch-up: filling {len(symbols)} symbols from {start} to {end}")
    filled = 0
    for i, sym in enumerate(symbols, 1):
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), interval="1d")
            if hist.empty:
                continue
            conn = get_db()
            cur = conn.cursor()
            for idx, row in hist.iterrows():
                d = idx.date().isoformat()
                close = row["Close"]
                vol = row["Volume"]
                if close and close == close:  # not NaN
                    cur.execute("""
                        INSERT OR REPLACE INTO daily_closes (symbol, date, close, volume)
                        VALUES (?, ?, ?, ?)
                    """, (sym, d, float(close), int(vol) if vol == vol else None))
                    filled += 1
            conn.commit()
            conn.close()
            if i % 25 == 0:
                print(f"  …{i}/{len(symbols)}", flush=True)
            time.sleep(0.2)
        except Exception as e:
            print(f"  {sym}: {e}")
    print(f"Catch-up: done. Wrote {filled} daily bars.")

def background_updater():
    """Main background loop. Respects background_paused setting while Tool 2 is active."""
    last_collapse = datetime.now(UK).date()
    last_holdings_daily = None
    while True:
        try:
            # Pause while Tool 2 is running a script
            if get_setting("background_paused") == "1":
                print("Background paused (Tool 2 active)")
                time.sleep(5)
                continue

            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT symbol FROM index_constituents")
            symbols = [row[0] for row in cur.fetchall()]
            conn.close()
            print(f"Background update + snapshots for {len(symbols)} symbols…")
            for sym in symbols:
                q = fetch_quote(sym)
                if q:
                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO index_quotes
                            (symbol, price, change, change_pct, volume, avg_volume, name, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(symbol) DO UPDATE SET
                            price = excluded.price,
                            change = excluded.change,
                            change_pct = excluded.change_pct,
                            volume = excluded.volume,
                            avg_volume = COALESCE(excluded.avg_volume, index_quotes.avg_volume),
                            name = excluded.name,
                            last_update = excluded.last_update
                    """, (
                        q["symbol"], q["price"], q["change"], q["change_pct"],
                        q["volume"], q["avg_volume"], q["name"],
                        datetime.now(timezone.utc).isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    write_snapshot(q)
                time.sleep(1.5)
            today = datetime.now(UK).date()
            if today != last_collapse:
                collapse_old_snapshots()
                last_collapse = today
            if last_holdings_daily != today:
                update_holdings_marks()
                last_holdings_daily = today
            print("Background cycle complete")
        except Exception as e:
            print("Background error:", e)
        time.sleep(30)

def update_holdings_marks():
    """Once-per-day: advance day offsets, freeze prior marks, apply auto-sell rules."""
    from holdings import is_uk_trading_day, close_holding_internal
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM holdings WHERE status = 'open'")
    opens = cur.fetchall()
    today = datetime.now(UK).date()
    target_pct = float(get_setting("tracker_close_target", "3"))

    for h in opens:
        entry = datetime.strptime(h["entry_date"], "%Y-%m-%d").date()
        trading_days = 0
        d = entry
        while d <= today:
            if is_uk_trading_day(d):
                trading_days += 1
            d += timedelta(days=1)
        day_offset = trading_days - 1
        if day_offset < 0 or day_offset > 13:
            continue

        cur.execute("SELECT price FROM index_quotes WHERE symbol = ?", (h["symbol"],))
        row = cur.fetchone()
        if not row or not row["price"]:
            continue
        price = row["price"]
        proceeds = h["shares"] * price
        pnl_net = proceeds - h["notional"]

        cur.execute("""
            INSERT OR REPLACE INTO holdings_marks
            (holding_id, day_offset, mark_date, price, pnl_net)
            VALUES (?, ?, ?, ?, ?)
        """, (h["id"], day_offset, today.isoformat(), price, pnl_net))

        if pnl_net / h["notional"] * 100 >= target_pct or day_offset >= 13:
            reason = "target" if pnl_net / h["notional"] * 100 >= target_pct else "expiry"
            close_holding_internal(h["id"], price, reason)

    conn.commit()
    conn.close()