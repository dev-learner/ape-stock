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

app = Flask(__name__)
app.register_blueprint(main_bp)
app.register_blueprint(scripts_bp)
app.register_blueprint(holdings_bp)

def ensure_screener_metrics():
    """Run screener metrics update if it has not been run since the last trading day."""
    from db import get_db
    UK = ZoneInfo("Europe/London")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = 'screener_metrics_updated'")
    row = cur.fetchone()
    conn.close()

    last = None
    if row and row[0]:
        try:
            last = datetime.fromisoformat(row[0])
        except Exception:
            last = None

    now = datetime.now(UK)
    needs_run = last is None or (now - last) > timedelta(hours=20)

    if needs_run:
        print("Screener metrics stale or missing — updating…")
        script = Path(__file__).parent / "scripts" / "update_screener_metrics.py"
        try:
            subprocess.run([sys.executable, str(script)], check=False, timeout=120)
        except Exception as e:
            print(f"Screener metrics update failed: {e}")
    else:
        print(f"Screener metrics up to date (last={last})")

if __name__ == "__main__":
    init_db()
    catchup_daily_closes()
    ensure_screener_metrics()
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=5050, debug=False)