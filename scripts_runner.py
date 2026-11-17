# scripts_runner.py
import subprocess
import sys
import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from db import get_setting, set_setting

SCRIPTS_DIR = Path(__file__).parent / "scripts"
bp = Blueprint("scripts", __name__)

@bp.route("/scripts/list")
def scripts_list():
    if not SCRIPTS_DIR.exists():
        return jsonify([])
    files = sorted([f.name for f in SCRIPTS_DIR.glob("*.py")])
    return jsonify(files)

@bp.route("/scripts/run", methods=["POST"])
def scripts_run():
    data = request.get_json(silent=True) or {}
    name = data.get("script", "").strip()
    if not name or not name.endswith(".py") or "/" in name or "\\" in name:
        return jsonify({"error": "Invalid script name"}), 400
    script_path = SCRIPTS_DIR / name
    if not script_path.exists():
        return jsonify({"error": "Script not found"}), 404
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,          # raised for longer scripts
            cwd=str(SCRIPTS_DIR),
            encoding="utf-8",
            errors="replace"
        )
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Script timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/scripts/meta")
def scripts_meta():
    """Return DESC and RUN comments from a script."""
    name = request.args.get("name", "").strip()
    if not name or not name.endswith(".py") or "/" in name or "\\" in name:
        return jsonify({"name": name, "desc": "", "run": ""})

    path = SCRIPTS_DIR / name
    if not path.exists():
        return jsonify({"name": name, "desc": "", "run": ""})

    desc = ""
    run = ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines()[:30]:
            line = line.strip()
            if line.startswith("# DESC:"):
                desc = line[7:].strip()
            elif line.startswith("# RUN:"):
                run = line[6:].strip()
            if desc and run:
                break
    except Exception:
        pass

    return jsonify({"name": name, "desc": desc, "run": run})

# --- Pause control ---
@bp.route("/scripts/pause", methods=["POST"])
def scripts_pause():
    """Set or clear the background pause flag."""
    data = request.get_json(silent=True) or {}
    paused = bool(data.get("paused"))
    set_setting("background_paused", "1" if paused else "0")
    return jsonify({"ok": True, "paused": paused})

# --- Script run counts ---
def _load_counts():
    raw = get_setting("script_run_counts", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _save_counts(counts):
    set_setting("script_run_counts", json.dumps(counts))

@bp.route("/scripts/counts")
def scripts_counts():
    return jsonify(_load_counts())

@bp.route("/scripts/increment", methods=["POST"])
def scripts_increment():
    data = request.get_json(silent=True) or {}
    name = data.get("script", "").strip()
    if not name:
        return jsonify({"error": "script required"}), 400
    counts = _load_counts()
    counts[name] = counts.get(name, 0) + 1
    _save_counts(counts)
    return jsonify({"ok": True, "count": counts[name]})

@bp.route("/scripts/clear_counts", methods=["POST"])
def scripts_clear_counts():
    set_setting("script_run_counts", "{}")
    return jsonify({"ok": True})

@bp.route("/scripts/delete", methods=["POST"])
def scripts_delete():
    """Delete one or more scripts from the scripts directory."""
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
        path = SCRIPTS_DIR / name
        if not path.exists():
            errors.append(f"Not found: {name}")
            continue
        try:
            path.unlink()
            deleted.append(name)
        except Exception as e:
            errors.append(f"{name}: {e}")

    return jsonify({"ok": True, "deleted": deleted, "errors": errors})