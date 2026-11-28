# scripts/create_handover_prompt.py
# NAME: Generate Handover Prompt
# DESC: Prints a ready-to-use handover prompt for continuing ape-stock development.
# DETAIL: Outputs a standardised prompt that points a new assistant at the GitHub repository, lists the key entry-point files (including new Grok-It! and Screens-related files), and restates the project rules (UK-only, modular changes, complete-file returns, etc.). Read-only; makes no changes to the database or filesystem.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: setup

"""
Generate Handover Prompt
------------------------
Prints a complete handover prompt to stdout so it can be copied from the
Tool 2 output panel and pasted into a new conversation.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

REPO_URL = "https://github.com/dev-learner/ape-stock"
RAW_BASE = "https://raw.githubusercontent.com/dev-learner/ape-stock/main"

def main():
    prompt = f"""You are continuing development of a local Flask application called ape-stock.

The complete, up-to-date source is in the public repository:
{REPO_URL}

Key entry points (raw links):
- {RAW_BASE}/app.py
- {RAW_BASE}/background.py
- {RAW_BASE}/data.py
- {RAW_BASE}/db.py
- {RAW_BASE}/grokit_runner.py
- {RAW_BASE}/holdings.py
- {RAW_BASE}/portfolio.py
- {RAW_BASE}/routes_admin.py
- {RAW_BASE}/routes_core.py
- {RAW_BASE}/routes_fundamentals.py
- {RAW_BASE}/routes_market.py
- {RAW_BASE}/routes_screener.py
- {RAW_BASE}/routes_screens.py
- {RAW_BASE}/routes_settings.py
- {RAW_BASE}/routes_status.py
- {RAW_BASE}/routes_tools.py
- {RAW_BASE}/routes.py
- {RAW_BASE}/scripts_runner.py

- {RAW_BASE}/static/style.css

- {RAW_BASE}/static/js/core.js
- {RAW_BASE}/static/js/dashboard.js
- {RAW_BASE}/static/js/tool2.js
- {RAW_BASE}/static/js/tool3.js
- {RAW_BASE}/static/js/tool4.js
- {RAW_BASE}/static/js/tool5.js
- {RAW_BASE}/static/js/tool6.js
- {RAW_BASE}/static/js/tool7.js
- {RAW_BASE}/static/js/tool8.js
- {RAW_BASE}/static/js/tool9.js
- {RAW_BASE}/static/js/tool10.js
- {RAW_BASE}/static/js/tool11.js
- {RAW_BASE}/static/js/tool12.js

- {RAW_BASE}/templates/index.html
- {RAW_BASE}/templates/settings.html

Directories of note:
- {RAW_BASE}/grokit/          (Grok-It! templates)
- {RAW_BASE}/scripts/         (Tool 2 ad-hoc scripts, database updates, backtests, table dumps, ad-hoc scripts, general)

APE-STOCK OVERVIEW:
ape-stock's goal, focusing solely on the FTSE 100 and FTSE 250 indexes, is to present the user with a list of potential growth and recovery stocks that are likely to do well in the short (2-3 weeks) to medium term (3-6 months).
ape-stock builds the presented list by ranking all stocks (1 - 351) known as the base rank. Overlaying the base rank with different screeners (based on technical analysis and or fundamental criteria) results in a second rank specific to the screener applied.
by scoring the results and using weights to determine the importance of that score. Summing the resulting scores from all screeners provides the final list of potential candidates for the user to consider.

IMPORTANT!:
1. Always make sure code is fully commented.
2. Always remove redundant code.
3. Avoid in-line CSS - use: {RAW_BASE}/static/style.css
4. If an edit is 'minor' return the complete function.
5. If an edit is more than 'minor' return the complete file.
6. NEVER return snippets of code.

FIRST STEPS:
1. Examine: The repository commits, directory and structure, and the code within each file.
2. NOTE: The comment header lines in all {RAW_BASE}/scripts/ files.
2. Confirm: Your understanding of ape-stock.
3. Confirm: 'Where we are' in the development cycle and what we're currently working on.
4. Any questions? Please ask.

"""
    print(prompt)

if __name__ == "__main__":
    main()