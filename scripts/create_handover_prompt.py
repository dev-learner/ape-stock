# scripts/create_handover_prompt.py
# NAME: Generate Handover Prompt
# DESC: Prints a ready-to-use handover prompt for continuing ape-stock development.
# DETAIL: Outputs a standardised prompt that points a new assistant at the GitHub repository, lists the key entry-point files, and restates the project rules (UK-only, modular changes, complete-file returns, etc.). Read-only; makes no changes to the database or filesystem.
# ALLOW_DELETE: 1
# RUN: Tool2

"""
Generate Handover Prompt
------------------------
Prints a complete handover prompt to stdout so it can be copied from the
Tool 2 output panel and pasted into a new conversation.

The prompt includes:
- Repository URL and raw links to the main source files
- Instructions to examine the Dashboard and repository structure
- The standing project rules (FTSE-only, modular changes, full-file returns)
- The required opening checklist for a new session

No database access and no side effects.
"""

import sys

# Ensure UTF-8 output so Tool 2 receives the text correctly
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
- {RAW_BASE}/static/js/dashboard.js
- {RAW_BASE}/static/js/tool3.js
- {RAW_BASE}/static/js/tool4.js
- {RAW_BASE}/static/js/tool8.js
- {RAW_BASE}/templates/index.html
- {RAW_BASE}/templates/settings.html

To gain a complete understanding of ape-stock examine the Dashboard page, the repository structure and the code within each file.

Keep the UK-only focus: FTSE 100 & FTSE 250.

Use small modular changes (shared-core philosophy).

Remove redundant code.

IMPORTANT!:
1. Always make sure code is fully commented.
2. If an edit is 'minor' return the complete function.
3. If an edit is more than 'minor' return the complete file.
4. NEVER return snippets of code.

Continue from this exact state and before anything else:
1. Confirm your understanding of ape-stock.
2. Where we are in the development cycle (what are we currently working on and what's next?).
3. Any initial questions - Please ask.
4. Welcome to the ape-stock dev team!
"""
    print(prompt)

if __name__ == "__main__":
    main()