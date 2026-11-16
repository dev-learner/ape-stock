ape-stockLocal Flask + SQLite decision-support tool for discretionary dip-buying and swing trading on FTSE 100 & FTSE 250 names only.It started as a simple “buy the big fallers” dashboard and has evolved into a more considered system: Screener persistence ranking, holdings tracking with live marks, ad-hoc analysis scripts, and a quiet background updater that keeps daily closes and 5-minute snapshots current. The user is still learning. The strategy is shifting from pure mechanical dip-buying toward “buy success after serious analysis”.UK only. No US stocks, no crypto, no meme names outside the FTSE universe. If it isn’t in the FTSE 100 or 250, it doesn’t exist here.
Features / ToolsTool
Name
Purpose
1
Dashboard
Overview, notes, status of everything
2
Ad-Hoc Scripts
Run analysis, back-tests, metrics updates, dumps
3
Holdings Tracker
Positions, live P&L, day marks, charts
4
Screener
Safe-bet names + daily rank / persistence
7
Rules
Parameters that drive Screener & Hit
8
Risers / Fallers
Day’s movers with Hit score
9
Settings
Persistable thresholds and limits
10
Admin
Housekeeping

Background process refreshes quotes, writes 5-min snapshots, collapses old data into daily_closes, and advances holdings marks.Quick StartWindows (recommended):bat

run.bat

This will:Create a venv if needed
Install requirements
Start Flask on http://127.0.0.1:5050
Open the browser once the port is listening

Manual:bash

python -m venv venv
venv\Scripts\activate          # or source venv/bin/activate
pip install -r requirements.txt
python app.py

Database (ape_stock.db) is created automatically on first run. Constituents are refreshed from the usual sources; daily closes are back-filled as needed.RequirementsPython 3.11+
See requirements.txt (Flask, yfinance, pandas, etc.)
Internet for the first run / constituent refresh

Project Layout

app.py              # Flask entry + background thread
background.py       # Quote updater, snapshots, holdings marks
db.py               # SQLite helpers + schema
routes.py           # Main routes (status, screener, tool endpoints)
holdings.py         # Holdings tracker blueprint
scripts_runner.py   # Tool 2 backend
scripts/            # Ad-hoc analysis & update scripts
static/             # CSS + JS (dashboard, tool3, tool4, tool8…)
templates/          # index.html, settings.html

Tool 2 (Ad-Hoc Scripts)Scripts live in scripts/ and are discovered automatically. Each script can declare:python

# DESC: One-line description shown as tooltip
# RUN: Tool2   (or “From venv/cmd (interactive prompts)”)

Tool 2 pauses the background updater while active so long-running scripts don’t fight the database. Usage counts are tracked.Development NotesShared-core philosophy: small modular changes.
Settings live in the app_settings table and are editable via Tool 9.
Ranking parameters (rank_window, rank_presence, rank_cutoff) drive Tool 4 persistence.
Screener metrics are refreshed via scripts/update_screener_metrics.py (also called on startup if stale).

DisclaimerThis is a personal research and learning tool. It is not financial advice. Past persistence or back-test results are not guarantees of future performance. You are responsible for your own decisions and capital.Built for the FTSE, by someone still figuring out the FTSE.

