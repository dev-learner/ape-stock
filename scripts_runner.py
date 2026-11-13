# scripts_runner.py
import subprocess
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify

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
            timeout=180,
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
