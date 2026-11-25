# routes_admin.py
# Admin bug reporting routes extracted from the original routes.py.

from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify
from db import get_db

UK = ZoneInfo("Europe/London")
bp = Blueprint("admin", __name__)

@bp.route("/admin/bugs", methods=["GET", "POST"])
def bugs():
    """List open bugs or create a new bug report."""
    conn = get_db()
    cur = conn.cursor()
    if request.method == "POST":
        data = request.get_json() or {}
        cur.execute("""
            INSERT INTO bugettes (description, expected, tool, created)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("description", "").strip(),
            data.get("expected", "").strip(),
            data.get("tool", "").strip(),
            datetime.now(UK).isoformat()
        ))
        conn.commit()
        conn.close()
        return jsonify({"ok": True})

    cur.execute("SELECT * FROM bugettes WHERE status = 'open' ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@bp.route("/admin/bugs/prompt")
def bug_prompt():
    """Generate a handover-style prompt containing open bugs."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bugettes WHERE status = 'open' ORDER BY id")
    bugs = cur.fetchall()
    conn.close()

    if not bugs:
        prompt = "No open bugs."
    else:
        prompt = "The following errors have been reported:\n\n"
        for b in bugs:
            prompt += f"- Tool: {b['tool'] or '—'}\n"
            prompt += f"  Description: {b['description']}\n"
            prompt += f"  Expected: {b['expected'] or '—'}\n\n"
        prompt += """1 - Use the latest files from ape-stock's repo. (https://github.com/dev-learner/ape-stock)
2 - IMPORTANT - For any file that is edited:
a) - If the edit is 'minor' return the complete function.
b) - If the edit is more than 'minor' return the complete file.
3 - Confirm your understanding of the 'issues'
4 - Any initial questions before coding- Please ask."""

    return jsonify({"prompt": prompt})

@bp.route("/admin/bugs/signoff", methods=["POST"])
def bug_signoff():
    """Mark selected bugs as closed."""
    data = request.get_json() or {}
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"ok": True})

    conn = get_db()
    cur = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    cur.execute(f"""
        UPDATE bugettes
        SET status = 'closed'
        WHERE id IN ({placeholders})
    """, ids)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})