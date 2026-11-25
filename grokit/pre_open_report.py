# grokit/pre_open_report.py
# NAME: Pre-Open Market Report
# DESC: Generates a concise pre-open briefing covering overnight indexes, key drivers, sector impact and portfolio exposure.
# DETAIL: Builds a signal-only morning report. Includes overnight index performance, material news and political developments, commodities and rates (when relevant), conditional sector impact rules, and highlights any open holdings exposed to mentioned sectors. Omits any section with no market-relevant content. Appends source links for major stories when available. Read-only with respect to the local database.
# ALLOW_DELETE: 1
# RUN: Tool11

"""
Pre-Open Market Report
----------------------
Produces a tight, decision-oriented briefing for the London open.

The report is adaptive:
- Sections with no market-relevant content are omitted.
- Portfolio holdings are highlighted only when a mentioned sector matches an open position.
- Source links are included for major stories when available.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    print("ERROR: python-dotenv is not installed.")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package is not installed.")
    sys.exit(1)

UK = ZoneInfo("Europe/London")

SYSTEM_PROMPT = """You are a concise FTSE pre-open market analyst.
The date supplied by the user is today. Generate the report; do not refuse on date grounds.
Produce a signal-only report. Omit any section that has no market-relevant content.
Never write "none" or include non-market news.
Use exactly the structure and rules provided in the user message.
When a sector is mentioned and the user supplies open holdings in that sector, highlight them under Portfolio notes.
Include a Sources section at the end only if you have real URLs for the major stories."""

def main():
    api_key = os.getenv("XAI_API_KEY")
    base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    model = os.getenv("DEFAULT_MODEL", "grok-4")

    if not api_key:
        print("ERROR: XAI_API_KEY not found in .env")
        return

    today = datetime.now(UK).strftime("%A %d %B %Y")

    user_prompt = f"""The current date is {today}. This is today, not a future date.
Generate the Pre-Open Market Report for today ({today}).

Use real overnight market action and material news as you know them.
Do not refuse on the grounds of the date.

Use this exact structure and rules:

Pre-Open Market Report — {today}

Expected FTSE open: [Up / Down / Flat]

Previous London close: FTSE 100 closed at [price] ([+/-]%)
[Only if material]

Overnight Indexes: [Up / Down / Flat / Mixed]
- Dow:       [Up/Down/Flat]  [close]  ([+/-]%)
- S&P 500:   [Up/Down/Flat]  [close]  ([+/-]%)
- Nasdaq:    [Up/Down/Flat]  [close]  ([+/-]%)
- Nikkei:    [Up/Down/Flat]  [close]  ([+/-]%)
- Hang Seng: [Up/Down/Flat]  [close]  ([+/-]%)

Key Drivers
[Only market-relevant items]
1. Market news: ...
2. Global events: ...
3. Political / policy: ...

Commodities & Rates
[Only material moves]

Implications for the FTSE
[Only if specific]

Sector impact
[Only triggered rules]
- Oil ≥ +1.5 %: Energy and oil-services names should see support; airlines, chemicals and some industrials may lag.
- Oil ≤ –1.5 %: Energy names pressured; airlines and chemicals relatively better.
- Gold ≥ +1.5 %: Precious-metal miners supported; often accompanies a more cautious risk tone.
- UK 10y gilt yield ≥ +5 bp: Banks can benefit; housebuilders, utilities and long-duration growth names usually pressured.
- UK 10y gilt yield ≤ –5 bp: Support for housebuilders and rate-sensitive sectors; banks may lag.
- Major US tech down ≥ 2 %: Cyclicals (miners, banks, industrials) usually weaker; defensives relatively better.
- Major US tech up ≥ 2 %: Risk appetite improves; cyclicals and growth-oriented names supported.

Portfolio notes
[Only if a mentioned sector matches an open holding — list them]

Risk notes
[Only if specific]

Summary
[One or two sentences]

Sources
[Only if you have real URLs for the major stories]

Rules:
- Omit any section or line with no market-relevant content.
- Never write "none".
- Be factual and concise.
- Base the report on real overnight market action and material news.
- The date given is today. Generate the report.
"""

    print(f"Generating Pre-Open Market Report for {today}...\n")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        report = response.choices[0].message.content.strip()
        print(report)
    except Exception as e:
        print("ERROR: API call failed")
        print(str(e))

if __name__ == "__main__":
    main()