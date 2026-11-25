# scripts/create_handover_prompt.py
# NAME: Generate Handover Prompt
# DESC: Prints a ready-to-use handover prompt for continuing ape-stock development.
# DETAIL: Outputs a standardised prompt that points a new assistant at the GitHub repository, lists the key entry-point files (including new Grok-It! and Screens-related files), and restates the project rules (UK-only, modular changes, complete-file returns, etc.). Read-only; makes no changes to the database or filesystem.
# ALLOW_DELETE: 1
# RUN: Tool2

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
- {RAW_BASE}/routes.py
- {RAW_BASE}/holdings.py
- {RAW_BASE}/background.py
- {RAW_BASE}/data.py
- {RAW_BASE}/db.py
- {RAW_BASE}/portfolio.py
- {RAW_BASE}/grokit_runner.py
- {RAW_BASE}/scripts_runner.py
- {RAW_BASE}/static/js/dashboard.js
- {RAW_BASE}/static/js/tool2.js
- {RAW_BASE}/static/js/tool3.js
- {RAW_BASE}/static/js/tool4.js
- {RAW_BASE}/static/js/tool8.js
- {RAW_BASE}/static/js/tool11.js
- {RAW_BASE}/templates/index.html
- {RAW_BASE}/templates/settings.html

Directories of note:
- {RAW_BASE}/grokit/          (Grok-It! templates)
- {RAW_BASE}/scripts/         (Tool 2 ad-hoc scripts, including recovery_screen.py and leader_run_analysis.py)

To gain a complete understanding of ape-stock examine the repository commits, structure and the code within each file.

Keep the UK-only focus: FTSE 100 & FTSE 250.

Use small modular changes (shared-core philosophy).

IMPORTANT!:
1. Always make sure code is fully commented.
2. Always remove redundant code.
3. Avoid in-line CSS - use: {RAW_BASE}/static/style.css
3. If an edit is 'minor' return the complete function.
4. If an edit is more than 'minor' return the complete file.
5. NEVER return snippets of code.

Continue from this exact state and before anything else:
1. Confirm your understanding of ape-stock.
2. Where we are in the development cycle (what are we currently working on and what's next?).
3. Any initial questions - Please ask.
"""
    print(prompt)

if __name__ == "__main__":
    main()