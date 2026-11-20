# data.py
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from db import get_db, get_ftse_state, save_ftse_state
import hashlib
from db import get_constituents_fingerprint, save_constituents_fingerprint

UK = ZoneInfo("Europe/London")
_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})

INDEX_SOURCES = {
    "100": "https://www.hl.co.uk/shares/stock-market-summary/ftse-100",
    "250": "https://www.hl.co.uk/shares/stock-market-summary/ftse-250",
}

def fetch_hl_index(base_url, pages=4):
    symbols = set()
    for page in range(1, pages + 1):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        try:
            r = _session.get(url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for row in soup.select("table tr"):
                cells = row.find_all("td")
                if not cells:
                    continue
                raw = cells[0].get_text(strip=True).strip()
                if not raw or raw.upper() in ("EPIC", "« PREVIOUS", "NEXT »", "PREVIOUS", "NEXT"):
                    continue
                if any(c in raw for c in "«»") or len(raw) > 12 or " " in raw:
                    continue
                epic = raw.rstrip(".")
                if epic.endswith(".A"):
                    epic = epic[:-2] + "-A"
                elif epic.endswith(".B"):
                    epic = epic[:-2] + "-B"
                elif epic.endswith(".C"):
                    epic = epic[:-2] + "-C"
                if not epic.upper().endswith(".L"):
                    epic = f"{epic}.L"
                symbols.add(epic)
        except Exception as e:
            print(f"HL scrape failed for {url}:", e)
    return symbols

def refresh_constituents():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM index_constituents")
    for key, url in INDEX_SOURCES.items():
        symbols = fetch_hl_index(url)
        for sym in symbols:
            cur.execute("INSERT OR REPLACE INTO index_constituents (index_key, symbol) VALUES (?, ?)", (key, sym))
        print(f"Loaded {len(symbols)} symbols for FTSE {key}")
    conn.commit()
    conn.close()

def fetch_quote(symbol):
    if not isinstance(symbol, str):
        return None
    symbol = symbol.strip()
    if any(c in symbol for c in "«»") or "Previous" in symbol or "Next" in symbol:
        return None
    if symbol.endswith("..L"):
        symbol = symbol.replace("..L", ".L")
    if ".A.L" in symbol:
        symbol = symbol.replace(".A.L", "-A.L")
    if ".B.L" in symbol:
        symbol = symbol.replace(".B.L", "-B.L")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    try:
        r = _session.get(url, params={"range": "1d", "interval": "1d"}, timeout=10)
        r.raise_for_status()
        meta = r.json()["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose")
        change = price - prev if price and prev else None
        change_pct = (change / prev * 100) if change and prev else None
        return {
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_pct": change_pct,
            "volume": meta.get("regularMarketVolume"),
            "avg_volume": meta.get("averageDailyVolume3Month") or meta.get("averageDailyVolume10Day"),
            "name": meta.get("shortName") or meta.get("longName") or symbol,
        }
    except Exception as e:
        print(f"quote error {symbol}: {e}")
        return None

def fetch_quotes(symbols):
    results = []
    for sym in symbols:
        q = fetch_quote(sym)
        if q:
            results.append(q)
        time.sleep(0.15)
    return results

def fetch_news(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search"
        r = _session.get(url, params={"q": symbol, "newsCount": 5}, timeout=10)
        r.raise_for_status()
        items = r.json().get("news", [])[:5]
        result = []
        for it in items:
            result.append({
                "title": it.get("title"),
                "time": it.get("providerPublishTime"),
                "url": it.get("link") or it.get("url")
            })
        return result
    except Exception as e:
        print(f"news error {symbol}: {e}")
        return []

def fetch_ftse():
    """Return live FTSE 100 status using Yahoo chart history."""
    try:
        r = _session.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/%5EFTSE",
            params={"range": "10d", "interval": "1d"},
            timeout=10
        )
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        timestamps = result.get("timestamp", [])
        closes = result["indicators"]["quote"][0].get("close", [])

        # Build clean list of (date, close)
        pairs = []
        for ts, close in zip(timestamps, closes):
            if close is not None and close == close:  # not NaN
                d = datetime.fromtimestamp(ts, UK).date()
                pairs.append((d, float(close)))

        if not pairs:
            raise ValueError("No valid closes")

        # Most recent close is current (or last close if market closed)
        current = pairs[-1][1]
        previous = pairs[-2][1] if len(pairs) > 1 else current

        now_uk = datetime.now(UK)
        open_t = now_uk.replace(hour=8, minute=0, second=0, microsecond=0)
        close_t = now_uk.replace(hour=16, minute=30, second=0, microsecond=0)
        is_weekday = now_uk.weekday() < 5
        is_open = is_weekday and open_t <= now_uk < close_t

        # If market is open, prefer the meta regularMarketPrice if available
        meta = result.get("meta", {})
        if is_open and meta.get("regularMarketPrice"):
            current = float(meta["regularMarketPrice"])

        state = get_ftse_state()
        previous_was_up = state.get("previous_was_up")

        if previous is not None and state.get("previous_close") != previous:
            if state.get("previous_close") is not None and current is not None:
                previous_was_up = current >= state["previous_close"]
            save_ftse_state(previous, previous_was_up)

        return {
            "previous": previous,
            "current": current,
            "is_open": is_open,
            "previous_was_up": bool(previous_was_up) if previous_was_up is not None else None,
            "server_time": now_uk.isoformat()
        }
    except Exception as e:
        print("FTSE fetch error:", e)
        return {
            "previous": None,
            "current": None,
            "is_open": False,
            "previous_was_up": None,
            "server_time": None
        }

def _page1_fingerprint(url):
    """Fast fingerprint from the first page only."""
    try:
        r = _session.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        epics = []
        for row in soup.select("table tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            raw = cells[0].get_text(strip=True).strip()
            if raw and len(raw) <= 12 and " " not in raw and "«" not in raw:
                epics.append(raw)
        epics.sort()
        return hashlib.md5("|".join(epics).encode()).hexdigest()
    except Exception as e:
        print("Fingerprint failed:", e)
        return None

def refresh_constituents_if_needed():
    """Only full-scrape when the page-1 fingerprint has changed."""
    fp100 = _page1_fingerprint(INDEX_SOURCES["100"])
    fp250 = _page1_fingerprint(INDEX_SOURCES["250"])
    if not fp100 or not fp250:
        print("Fingerprint check failed — skipping refresh")
        return

    current_fp = f"{fp100}:{fp250}"
    stored_fp = get_constituents_fingerprint()

    if current_fp == stored_fp:
        print("Constituents unchanged — skipping full scrape")
        return

    print("Constituents changed — running full refresh")
    refresh_constituents()          # existing full scrape
    save_constituents_fingerprint(current_fp)