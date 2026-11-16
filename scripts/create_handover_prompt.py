# scripts/create_handover_prompt.py
# DESC: Generate a compact handover-prompt.txt that points at the public GitHub repo
# RUN: Tool2

from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "handover-prompt.txt"

REPO_URL = "https://github.com/dev-learner/ape-stock"
RAW_BASE = "https://raw.githubusercontent.com/dev-learner/ape-stock/main"

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

To gain a complete understanding of ape-stock, its goals and its components (tools 1-10) study the Dashboard page and the repository structure.

Keep the UK-only focus: FTSE 100 & FTSE 250.

Use small modular changes (shared-core philosophy).

Remove redundant code.

IMPORTANT - If you edit a file:
1. Always make sure code is fully documented.
2. If there is a 'minor' change in part of a function, or block of code, return the complete function (or block of code).
3. If the edit is more than 'minor' return the complete file.
4. NEVER return snippets of code.

Continue from this exact state.

Before anything else:
1. Confirm your understanding of ape-stock.
2. Where we are in the development cycle (what are we currently working on?).
3. Any initial questions - Please ask.
"""

OUT.write_text(prompt, encoding="utf-8")
print(f"Wrote {OUT}")
print(f"Prompt size: {len(prompt):,} characters")