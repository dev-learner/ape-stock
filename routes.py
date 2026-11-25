# routes.py
# Compatibility shim after the routes refactor.
# The original large file has been split into focused modules.
# This file re-exports the core blueprint so any lingering imports continue to work.
# Prefer importing from the specific routes_* modules in new code.

from routes_core import bp