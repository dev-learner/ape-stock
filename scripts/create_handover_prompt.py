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

Current goals, tech stack, design decisions and todo items live on the Dashboard page of the running app.

===== DIRECTORY STRUCTURE =====
{build_tree()}

===== FILE CONTENTS =====
{file_blocks()}

Continue from this exact state. Prefer small, modular, well-commented changes. Keep the UK-only focus and the shared-core philosophy.
"""

OUT.write_text(prompt, encoding="utf-8")
print(f"Wrote {OUT}")