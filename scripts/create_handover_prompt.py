# scripts/create_handover_prompt.py
# DESC: Generate handover-prompt.txt with full source tree and file contents
# RUN: Tool2

from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "handover-prompt.txt"

# Everything we want (explicit so venv, __pycache__, db, etc. are excluded)
INCLUDE_DIRS = ["templates", "static", "scripts"]
INCLUDE_ROOT_FILES = [
    "app.py",
    "background.py",
    "data.py",
    "db.py",
    "holdings.py",
    "routes.py",
    "scripts_runner.py",
    "requirements.txt",
    "run.bat",
    "set-env.bat",
]

def should_include(path: Path) -> bool:
    if path.name.startswith(".") or path.name == "__pycache__":
        return False
    if path.suffix in {".pyc", ".db", ".txt"} and path.name != "requirements.txt":
        return False
    return True

def build_tree():
    lines = ["ape-stock/"]
    # root files
    for name in sorted(INCLUDE_ROOT_FILES):
        p = ROOT / name
        if p.exists():
            lines.append(f"├── {name}")
    # directories
    for dname in INCLUDE_DIRS:
        d = ROOT / dname
        if not d.exists():
            continue
        lines.append(f"├── {dname}/")
        for f in sorted(d.rglob("*")):
            if f.is_file() and should_include(f):
                rel = f.relative_to(ROOT)
                indent = "│   " * (len(rel.parts) - 1)
                lines.append(f"{indent}├── {rel.name}")
    return "\n".join(lines)

def file_blocks():
    blocks = []
    # root files
    for name in INCLUDE_ROOT_FILES:
        p = ROOT / name
        if p.exists() and should_include(p):
            content = p.read_text(encoding="utf-8", errors="replace")
            blocks.append(f"===== FILE: {name} =====\n{content}\n")
    # directory files
    for dname in INCLUDE_DIRS:
        d = ROOT / dname
        if not d.exists():
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file() and should_include(f):
                rel = f.relative_to(ROOT).as_posix()
                content = f.read_text(encoding="utf-8", errors="replace")
                blocks.append(f"===== FILE: {rel} =====\n{content}\n")
    return "\n".join(blocks)

prompt = f"""You are continuing development of a local Flask application called ape-stock.

To gain a complete understanding of ape-stock, it's goals and it's components (tools 1-8) study tool1: 'Dashboard' page and it's contents.

Keep the UK-only focus: FTSE 100 & FTSE 250.

Use small modular changes (shared-core philosophy).

Remove redundant code.

IMPORTANT - If you edit a file: 
1: Always make sure code is fully documented.
2: If there is a 'minor' change in part of a function, or block of code, return the complete function (or block of code).
3: If the edit is more than 'minor' return the complete file.
4: NEVER return snippets of code.

===== DIRECTORY STRUCTURE =====
{build_tree()}

===== FILE CONTENTS =====
{file_blocks()}


Continue from this exact state. 

Before anything else:
1 - Confirm your understanding of ape-stock.
2 - Where we are in the devlopment cycle (what are we currently working on?).
3 - Any initial questions - Please ask.

"""

OUT.write_text(prompt, encoding="utf-8")
print(f"Wrote {OUT}")