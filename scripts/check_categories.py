# scripts/check_categories.py
# NAME: Check Categories
# DESC: Ensures every script has a # CATEGORY header, guessing from the filename when missing.
# DETAIL: Scans all .py files. Skips any that already contain a CATEGORY line. Uses simple filename rules for new scripts. Safe to re-run.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: setup

"""
Check Categories
----------------
Makes sure every script has a CATEGORY header.
Guesses a reasonable category from the filename when the line is missing.
"""

from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

def guess_category(name: str) -> str:
    """Return a category string based on the filename."""
    lower = name.lower()
    if lower.startswith("dump_"):
        return "dumps"
    if lower.startswith(("update_", "calculate_")):
        return "scores"
    if any(x in lower for x in ("backfill", "fetch", "populate")):
        return "data"
    if any(x in lower for x in ("test", "grid", "analysis", "backtest", "exdiv")):
        return "analysis"
    if any(x in lower for x in ("create_", "add_")):
        return "setup"
    return "uncategorised"

def main():
    updated = 0
    skipped = 0
    guessed = []

    for path in sorted(SCRIPTS_DIR.glob("*.py")):
        name = path.name
        text = path.read_text(encoding="utf-8", errors="replace")

        if "# CATEGORY:" in text:
            skipped += 1
            continue

        category = guess_category(name)
        lines = text.splitlines(keepends=True)

        # Insert after the last header comment in the first 30 lines
        insert_at = 0
        for i, line in enumerate(lines[:30]):
            if line.startswith("# "):
                insert_at = i + 1
            else:
                break

        lines.insert(insert_at, f"# CATEGORY: {category}\n")
        path.write_text("".join(lines), encoding="utf-8")

        print(f"Added '{category}' to {name}")
        guessed.append((name, category))
        updated += 1

    print(f"\nDone. Updated {updated}, already categorised {skipped}.")
    if guessed:
        print("Newly categorised:")
        for name, cat in guessed:
            print(f"  {name:<40} → {cat}")

if __name__ == "__main__":
    main()