# grokit_runner.py
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify
from db import get_setting, set_setting

GROKIT_DIR = Path(__file__).parent / "grokit"
bp = Blueprint("grokit", __name__)
UK = ZoneInfo("Europe/London")

@bp.route("/grokit/list")
def grokit_list():
    if not GROKIT_DIR.exists():
        return jsonify([])
    files = sorted([f.name for f in GROKIT_DIR.glob("*.py")])
    return jsonify(files)

@bp.route("/grokit/meta")
def grokit_meta():
    name = request.args.get("name", "").strip()
    if not name or not name.endswith(".py") or "/" in name or "\\" in name:
        return jsonify({"name": name, "friendly": name, "desc": "", "detail": "", "allow_delete": 1})

    path = GROKIT_DIR / name
    if not path.exists():
        return jsonify({"name": name, "friendly": name, "desc": "", "detail": "", "allow_delete": 1})

    friendly = name
    desc = ""
    detail = ""
    allow_delete = 1
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines()[:40]:
            line = line.strip()
            if line.startswith("# NAME:"):
                friendly = line[7:].strip() or name
            elif line.startswith("# DESC:"):
                desc = line[7:].strip()
            elif line.startswith("# DETAIL:"):
                detail = line[9:].strip()
            elif line.startswith("# ALLOW_DELETE:"):
                val = line[15:].strip()
                allow_delete = 1 if val == "1" else 0
    except Exception:
        pass

    return jsonify({
        "name": name,
        "friendly": friendly,
        "desc": desc,
        "detail": detail,
        "allow_delete": allow_delete
    })

@bp.route("/grokit/run", methods=["POST"])
def grokit_run():
    data = request.get_json(silent=True) or {}
    name = data.get("script", "").strip()
    if not name or not name.endswith(".py") or "/" in name or "\\" in name:
        return jsonify({"error": "Invalid template name"}), 400
    script_path = GROKIT_DIR / name
    if not script_path.exists():
        return jsonify({"error": "Template not found"}), 404
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(GROKIT_DIR.parent),
            encoding="utf-8",
            errors="replace"
        )
        # Record last-run
        last_runs = _load_last_runs()
        last_runs[name] = datetime.now(UK).isoformat()
        _save_last_runs(last_runs)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Template timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Counts & last-runs (separate keys from Tool 2) ---
def _load_counts():
    raw = get_setting("grokit_run_counts", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _save_counts(counts):
    set_setting("grokit_run_counts", json.dumps(counts))

def _load_last_runs():
    raw = get_setting("grokit_last_runs", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _save_last_runs(runs):
    set_setting("grokit_last_runs", json.dumps(runs))

@bp.route("/grokit/counts")
def grokit_counts():
    return jsonify(_load_counts())

@bp.route("/grokit/last_runs")
def grokit_last_runs():
    return jsonify(_load_last_runs())

@bp.route("/grokit/increment", methods=["POST"])
def grokit_increment():
    data = request.get_json(silent=True) or {}
    name = data.get("script", "").strip()
    if not name:
        return jsonify({"error": "script required"}), 400
    counts = _load_counts()
    counts[name] = counts.get(name, 0) + 1
    _save_counts(counts)
    return jsonify({"ok": True, "count": counts[name]})

@bp.route("/grokit/delete", methods=["POST"])
def grokit_delete():
    data = request.get_json(silent=True) or {}
    names = data.get("scripts", [])
    if not isinstance(names, list):
        return jsonify({"error": "scripts must be a list"}), 400

    deleted = []
    errors = []
    for name in names:
        name = str(name).strip()
        if not name or not name.endswith(".py") or "/" in name or "\\" in name or name.startswith("."):
            errors.append(f"Invalid name: {name}")
            continue
        path = GROKIT_DIR / name
        if not path.exists():
            errors.append(f"Not found: {name}")
            continue
        allow = 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines()[:40]:
                if line.strip().startswith("# ALLOW_DELETE:"):
                    allow = 1 if line.strip()[15:].strip() == "1" else 0
                    break
        except Exception:
            allow = 1
        if allow == 0:
            errors.append(f"Deletion not allowed: {name}")
            continue
        try:
            path.unlink()
            deleted.append(name)
        except Exception as e:
            errors.append(f"{name}: {e}")

    return jsonify({"ok": True, "deleted": deleted, "errors": errors})