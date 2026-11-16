**1. What is ape-stock?**

ape-stock is a local Flask + SQLite decision-support tool for discretionary dip-buying and swing trading, strictly limited to FTSE 100 & FTSE 250 constituents (UK-only focus).

It evolved from a simple “buy the big fallers” dashboard into a more considered system built around:

- **Tool 4 Screener**: relatively stable “safe-bet” names (above 50- & 200-day MAs, size floor, 3-month return, etc.) now with daily rank / persistence scoring.
- **Tool 8 Risers/Fallers**: day’s movers with a Hit score.
- **Tool 3 Holdings Tracker**: positions, live P&L, day marks, and charts.
- **Tool 2 Ad-Hoc Scripts**: workbench for analysis, back-tests, and metrics updates (pauses the background updater while running).
- Supporting tools for Rules, Settings, Admin, and a Dashboard overview.

A background process keeps quotes, 5-minute snapshots, daily closes, and holdings marks current. Settings live in `app_settings` and drive thresholds/ranking parameters. The philosophy is small modular changes, shared-core, removal of redundancy, and a learning-oriented shift from pure mechanical dip-buying toward “buy success after serious analysis.”

**2. Where we are in the development cycle**

Recent commits (13–16 Nov 2026) show the current focus:

- Persistence ranking introduced and iterated on for the Screener (Tool 4), with Settings controls for `rank_window`, `rank_presence`, and `rank_cutoff`.
- Hit threshold and other parameters now read from Settings.
- Tool 2 pauses background updates; collapsible toolbar, dashboard notes, Settings as Tool 9, and related UI polish.
- Handover prompt updated to point at the GitHub repo.

Core functionality is in place and operational. The Dashboard explicitly lists remaining To-Dos (visual badges on Tool 8 for current Screener names, live price/day-% on the Screener, acceleration cues, news/RNS flags, fully editable Rules feeding Screener & Hit, alerts, drag-and-drop, fundamentals rows, etc.). We are in an iterative enhancement / refinement phase: small modular improvements, wiring settings more thoroughly, and cleaning redundancy while preserving the FTSE-only shared-core approach.
