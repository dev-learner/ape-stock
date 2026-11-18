# app.py
import threading
from flask import Flask
from db import init_db
from background import catchup_daily_closes, background_updater
from routes import bp as main_bp
from scripts_runner import bp as scripts_bp
from holdings import bp as holdings_bp
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess
import sys
from pathlib import Path
from portfolio import bp as portfolio_bp

app = Flask(__name__)
app.register_blueprint(main_bp)
app.register_blueprint(scripts_bp)
app.register_blueprint(holdings_bp)
app.register_blueprint(portfolio_bp)

def _needs_run(key, hours=20):
    """Return True if the given app_settings timestamp is missing or older than `hours`."""
    from db import get_db
    UK = ZoneInfo("Europe/London")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()

    last = None
    if row and row[0]:
        try:
            last = datetime.fromisoformat(row[0])
        except Exception:
            last = None

    now = datetime.now(UK)
    return last is None or (now - last) > timedelta(hours=hours)

def ensure_screener_metrics():
    """Run screener metrics update if it has not been run since the last trading day."""
    if _needs_run("screener_metrics_updated"):
        print("Screener metrics stale or missing — updating…")
        script = Path(__file__).parent / "scripts" / "update_screener_metrics.py"
        try:
            subprocess.run([sys.executable, str(script)], check=False, timeout=180)
        except Exception as e:
            print(f"Screener metrics update failed: {e}")
    else:
        print("Screener metrics up to date")

def ensure_daily_ranks():
    """Run daily ranks update if stale."""
    if _needs_run("ranks_updated"):
        print("Daily ranks stale or missing — updating…")
        script = Path(__file__).parent / "scripts" / "update_daily_ranks.py"
        try:
            subprocess.run([sys.executable, str(script)], check=False, timeout=180)
        except Exception as e:
            print(f"Daily ranks update failed: {e}")
    else:
        print("Daily ranks up to date")

def ensure_fundamentals():
    """Run fundamentals update if stale."""
    if _needs_run("fundamentals_updated"):
        print("Fundamentals stale or missing — updating…")
        script = Path(__file__).parent / "scripts" / "update_fundamentals.py"
        try:
            subprocess.run([sys.executable, str(script)], check=False, timeout=300)
        except Exception as e:
            print(f"Fundamentals update failed: {e}")
    else:
        print("Fundamentals up to date")

if __name__ == "__main__":
    init_db()
    catchup_daily_closes()
    ensure_screener_metrics()
    ensure_daily_ranks()
    ensure_fundamentals()
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=5050, debug=False)