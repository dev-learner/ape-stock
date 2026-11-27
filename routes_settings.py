# routes_settings.py
# Settings get/save routes.
# Includes Recovery Screen parameters and Weightings with defaults.

from flask import Blueprint, render_template, request, jsonify
from db import get_setting, set_setting

bp = Blueprint("settings", __name__)

@bp.route("/settings")
def settings():
    """Render the settings page."""
    return render_template("settings.html")

@bp.route("/settings/save", methods=["POST"])
def settings_save():
    """Persist settings from the frontend."""
    data = request.get_json(silent=True) or {}

    # Tracker close target
    target = data.get("tracker_close_target")
    if target is not None:
        try:
            val = float(target)
            val = max(1, min(10, val))
            set_setting("tracker_close_target", val)
        except (TypeError, ValueError):
            pass

    # Valuation toggle
    if "use_valuation" in data:
        set_setting("use_valuation", "1" if str(data["use_valuation"]) in ("1", "true", "True") else "0")

    # All other settings stored as strings (including Recovery and Weightings)
    for key in (
        "listLimit", "riserPct", "fallerPct", "hitThreshold", "notional", "stampPct",
        "rsiOversold", "rsiOverbought", "rsiLength",
        "rank_window", "rank_presence", "rank_cutoff",
        "pe_min", "pe_max", "pb_max", "require_dividend",
        "cand_rank_max", "cand_pe_min", "cand_pe_max", "cand_pb_max", "cand_require_div",
        # Recovery
        "rec_lookback_months", "rec_min_drawdown", "rec_min_bounce",
        "rec_require_50ma", "rec_min_mcap", "rec_min_price",
        # Weightings
        "weight_base", "weight_ta", "weight_fund"
    ):
        if key in data and data[key] is not None:
            set_setting(key, str(data[key]))

    return jsonify({"ok": True})

@bp.route("/settings/get")
def settings_get():
    """Return current settings as JSON. Defaults are written if missing."""
    # Ensure Recovery and Weightings defaults exist
    defaults = {
        "rec_lookback_months": "12",
        "rec_min_drawdown": "35",
        "rec_min_bounce": "15",
        "rec_require_50ma": "1",
        "rec_min_mcap": "500",
        "rec_min_price": "50",
        "weight_base": "40",
        "weight_ta": "30",
        "weight_fund": "30",
    }
    for key, val in defaults.items():
        if get_setting(key) is None:
            set_setting(key, val)

    return jsonify({
        "tracker_close_target": get_setting("tracker_close_target", "3"),
        "listLimit": get_setting("listLimit", "25"),
        "riserPct": get_setting("riserPct", "3"),
        "fallerPct": get_setting("fallerPct", "3"),
        "hitThreshold": get_setting("hitThreshold", "50"),
        "notional": get_setting("notional", "500"),
        "stampPct": get_setting("stampPct", "0.5"),
        "rank_window": get_setting("rank_window", "35"),
        "rank_presence": get_setting("rank_presence", "50"),
        "rank_cutoff": get_setting("rank_cutoff", "12"),
        "pe_min": get_setting("pe_min", "5"),
        "pe_max": get_setting("pe_max", "40"),
        "pb_max": get_setting("pb_max", "4"),
        "require_dividend": get_setting("require_dividend", "0"),
        "use_valuation": get_setting("use_valuation", "0"),
        "rsiOversold": get_setting("rsiOversold", "30"),
        "rsiOverbought": get_setting("rsiOverbought", "70"),
        "rsiLength": get_setting("rsiLength", "7"),
        "cand_rank_max": get_setting("cand_rank_max", "12"),
        "cand_pe_min": get_setting("cand_pe_min", "5"),
        "cand_pe_max": get_setting("cand_pe_max", "40"),
        "cand_pb_max": get_setting("cand_pb_max", "4"),
        "cand_require_div": get_setting("cand_require_div", "0"),
        # Recovery
        "rec_lookback_months": get_setting("rec_lookback_months", "12"),
        "rec_min_drawdown": get_setting("rec_min_drawdown", "35"),
        "rec_min_bounce": get_setting("rec_min_bounce", "15"),
        "rec_require_50ma": get_setting("rec_require_50ma", "1"),
        "rec_min_mcap": get_setting("rec_min_mcap", "500"),
        "rec_min_price": get_setting("rec_min_price", "50"),
        # Weightings
        "weight_base": get_setting("weight_base", "40"),
        "weight_ta": get_setting("weight_ta", "30"),
        "weight_fund": get_setting("weight_fund", "30"),
    })