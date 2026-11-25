// static/js/dashboard.js
// Dashboard overview, notes, buy checklist, tool cards with To-Dos, schema and open items.
// Schema card is wide, left-aligned, shows latest values, and auto-refreshes with a flash on change.
window.Dashboard = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:8px; color:#aaa;">Loading dashboard…</div>`;

        // Fetch supporting data in parallel
        const [status, screener, holdings] = await Promise.all([
            fetch("/status").then(r => r.json()).catch(() => ({})),
            fetch("/screener").then(r => r.json()).catch(() => ({ rows: [] })),
            fetch("/holdings/list").then(r => r.json()).catch(() => ({ holdings: [] }))
        ]);

        const safeBets = (screener.rows || []).length;
        const openHoldings = (holdings.holdings || []).filter(h => h.status === "open");
        const openCount = openHoldings.length;
        let totalPnl = 0;
        openHoldings.forEach(h => {
            const marks = h.marks || [];
            const live = marks.length ? marks[marks.length - 1] : null;
            if (live && live.pnl_net != null) totalPnl += live.pnl_net;
        });

        const lastBg = status.last_background_update
            ? this.formatDate(status.last_background_update)
            : "—";
        const metricsUpdated = status.screener_metrics_updated
            ? this.formatDate(status.screener_metrics_updated)
            : "—";
        const dailyClosesLast = status.daily_closes_last || "—";
        const constituents = status.constituents || "—";

        // Load saved notes
        const savedNotes = localStorage.getItem("dashboard_notes") || "";

        container.innerHTML = `
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; padding:8px;">

                <!-- Overview -->
                <div class="card">
                    <h3>Ape-Stock Overview</h3>
                    <p>ape-stock is a personal decision-support tool for discretionary trading on the FTSE. It does not place trades or promise predictions.</p>
                    <p>Its job is to shrink a noisy universe into a short, ranked list of higher-quality candidates and then give the user a clean place to record and monitor the positions they actually take.</p><br>
                    <p><strong>Core workflow</strong></p>
                    <p>Risers / Fallers → Technical Analysis (persistence rank) → Fundamentals → Candidates (joined short-list) → Holdings Tracker → pre-buy checklist → Portfolio.</p><br>
                </div>

                <!-- Notes -->
                <div class="card" id="notes-card">
                    <h3>Notes</h3>
                    <div id="notes-display" style="white-space:pre-wrap; min-height:80px; font-size:0.9rem; line-height:1.45;">${this.escapeHtml(savedNotes) || "<span style='color:#666;'>No notes yet.</span>"}</div>
                    <textarea id="notes-edit" style="display:none; width:100%; min-height:120px; background:#0d1b2a; color:white; border:1px solid rgba(255,255,255,0.15); border-radius:4px; padding:8px; font-family:inherit; font-size:0.9rem; resize:vertical;">${savedNotes}</textarea>
                    <div style="text-align:right; margin-top:8px;">
                        <button id="notes-toggle" class="mini-btn" style="background:#1e5c3a;">Edit</button>
                    </div>
                </div>

                <!-- Buy Checklist -->
                <div class="card">
                    <h3>Buy Check List</h3>
                    <div class="section" style="font-size:0.88rem; line-height:1.5;">
                        <strong>1. Screener confirmation</strong><br>
                        □ Top tier of at least one screener<br>
                        □ Still meets core technical conditions<br>
                        □ Note rank / score & date<br><br>

                        <strong>2. Fundamental sense-check</strong><br>
                        □ PE / P/B not extreme<br>
                        □ Not a persistent loss-maker<br>
                        □ Adequate size & liquidity<br><br>

                        <strong>3. News & events (7–14 days)</strong><br>
                        □ No fresh profit warning / negative RNS<br>
                        □ No imminent earnings or ex-div surprise<br>
                        □ Sector news not contradictory<br><br>

                        <strong>4. Portfolio fit</strong><br>
                        □ Cash available<br>
                        □ Position size within limits<br>
                        □ Not over-exposed to sector<br><br>

                        <strong>5. Trade plan</strong><br>
                        □ Entry zone clear<br>
                        □ Invalidation level defined<br>
                        □ Rough target or review point<br><br>

                        <strong>6. Final go / no-go</strong><br>
                        □ Can explain why it is on the list<br>
                        □ Comfortable if it moves against me<br>
                        □ All boxes ticked (or consciously waived)
                    </div>
                </div>

                <!-- Tool 8 -->
                <div class="card">
                    <h3>Tool 8 — Risers / Fallers</h3>
                    <div class="section"><strong>Description</strong><br>
                    Surfaces the day’s biggest risers and fallers across the FTSE universe, with a simple Hit score. Primary discovery view for short-term moves.</div>
                    <div class="section"><strong>Data</strong><br>
                    Risers: <span id="dash-risers">—</span><br>
                    Fallers: <span id="dash-fallers">—</span></div>
                    <div class="section"><strong>To Do</strong>
                    <ul>
                        <li>Visual badge on names that are also current Screener safe-bets</li>
                        <li>Optional news / RNS flag</li>
                    </ul></div>
                </div>

                <!-- Tool 4 -->
                <div class="card">
                    <h3>Tool 4 — Screener</h3>
                    <div class="section"><strong>Description</strong><br>
                    Builds a relatively stable list of “safe-bet” names (above 50- & 200-day MAs, reasonable 3-month return, size floor). Default sort by 3 m %. Foundation for higher-quality dip-buys.</div>
                    <div class="section"><strong>Data</strong><br>
                    Safe bets: ${safeBets}<br>
                    Metrics last updated: ${metricsUpdated}</div>
                    <div class="section"><strong>To Do</strong>
                    <ul>
                        <li>Live Price + Day % (wired to auto-refresh)</li>
                        <li>Acceleration cue (3 m vs 6 m)</li>
                        <li>Persistence ranking display / filter</li>
                        <li>News / RNS presence flag</li>
                        <li>Optional “also down today” toggle</li>
                    </ul></div>
                </div>

                <!-- Tool 3 -->
                <div class="card">
                    <h3>Tool 3 — Holdings Tracker</h3>
                    <div class="section"><strong>Description</strong><br>
                    Tracks simulated (or real) positions taken from the Screener or Tool 8. Shows entry, live price, day marks, and three charts (90-day 5-min, today 5-min, 14-day daily). Supports discretionary monitoring and earlier exits.</div>
                    <div class="section"><strong>Data</strong><br>
                    Open holdings: ${openCount}<br>
                    Open P&L (net): £${totalPnl.toFixed(2)}</div>
                    <div class="section"><strong>To Do</strong>
                    <ul>
                        <li>Live update of current day’s +D mark</li>
                        <li>Drag-and-drop reordering</li>
                        <li>Expandable fundamentals row</li>
                        <li>Alerts (price, news, rank drop, MA loss)</li>
                    </ul></div>
                </div>

                <!-- Tool 7 -->
                <div class="card">
                    <h3>Tool 7 — Rules</h3>
                    <div class="section"><strong>Description</strong><br>
                    Central place for the parameters that drive the Screener, Hit score, and Tracker (thresholds, weights, targets). Currently shows hard-coded values; will become editable.</div>
                    <div class="section"><strong>Data</strong><br>
                    Parameters: hard-coded (see page)</div>
                    <div class="section"><strong>To Do</strong>
                    <ul>
                        <li>Make all thresholds / weights editable and persisted</li>
                        <li>Screener and Hit logic read from here</li>
                    </ul></div>
                </div>

                <!-- Tool 2 -->
                <div class="card">
                    <h3>Tool 2 — Ad-Hoc Scripts</h3>
                    <div class="section"><strong>Description</strong><br>
                    Run Python analysis and data-prep scripts (metrics update, back-tests, dumps, grid searches). The workbench for testing ideas before they move into the live tools.</div>
                    <div class="section"><strong>Data</strong><br>
                    (left as-is for now)</div>
                    <div class="section"><strong>To Do</strong>
                    <ul>
                        <li>Walk-forward version of persistence ranking</li>
                        <li>News-flag back-test</li>
                        <li>More sector / industry scripts</li>
                    </ul></div>
                </div>

                <!-- Tool 5 & 6 placeholders -->
                <div class="card">
                    <h3>Tool 5</h3>
                    <div class="section"><strong>Description</strong><br>Placeholder.</div>
                    <div class="section"><strong>Data</strong><br>—</div>
                    <div class="section"><strong>To Do</strong><br>—</div>
                </div>
                <div class="card">
                    <h3>Tool 6</h3>
                    <div class="section"><strong>Description</strong><br>Placeholder.</div>
                    <div class="section"><strong>Data</strong><br>—</div>
                    <div class="section"><strong>To Do</strong><br>—</div>
                </div>

                <!-- General -->
                <div class="card">
                    <h3>General</h3>
                    <div class="section">
                    Last background update: ${lastBg}<br>
                    Constituents: ${constituents}<br>
                    Screener metrics updated: ${metricsUpdated}<br>
                    Daily closes last date: ${dailyClosesLast}
                    </div>
                </div>

                <!-- Database Schema (wide + live) -->
                <div class="card" id="schema-card" style="grid-column:1 / -1;">
                    <h3>Database Schema <span id="schema-meta" style="font-size:0.8rem; color:#7fdbff; font-weight:normal;"></span></h3>
                    <div class="section" id="schema-content" style="font-size:0.82rem; line-height:1.35;">
                        Loading…
                    </div>
                </div>

                <!-- Tech Stack -->
                <div class="card">
                    <h3>Tech Stack</h3>
                    <div class="section">
                    Python 3 + Flask<br>
                    SQLite (WAL)<br>
                    yfinance<br>
                    Vanilla JS + CSS<br>
                    Canvas sparklines<br>
                    UK timezone aware<br>
                    <br>
                    <a href="https://github.com/dev-learner/ape-stock" target="_blank" style="color:#7fdbff;">GitHub repo</a>
                    </div>
                </div>

                <!-- Open Items -->
                <div class="card" style="grid-column:1 / -1;">
                    <h3>Open Items</h3>
                    <div class="section">
                        <ul>
                            <li>News / RNS presence or negative-keyword flag on screener and risers/fallers</li>
                            <li>Integrate or link reputable FTSE market analysis & commentary (primary candidates: Sharecast daily roundups + AJ Bell market commentary) for decision context beyond official RNS and Yahoo</li>
                            <li>Simple alerts for open positions (price drop, rank drop, MA loss)</li>
                            <li>Optional acceleration cue (3 m vs 6 m) on the technical screener</li>
                            <li>Walk-forward version of the persistence ranking for more realistic testing</li>
                            <li>Refactor routes.py: break the large file down and parse the code into individual components / blueprints (status, screener, tool endpoints, settings, etc.) to reduce complexity and improve maintainability</li>
                        </ul>
                    </div>
                </div>
        `;

        // Initial schema load
        this.refreshSchema();

        // Notes Edit / Save toggle
        const notesToggle = document.getElementById("notes-toggle");
        const notesDisplay = document.getElementById("notes-display");
        const notesEdit = document.getElementById("notes-edit");
        if (notesToggle && notesDisplay && notesEdit) {
            notesToggle.addEventListener("click", () => {
                const editing = notesEdit.style.display !== "none";
                if (editing) {
                    const val = notesEdit.value;
                    localStorage.setItem("dashboard_notes", val);
                    notesDisplay.innerHTML = this.escapeHtml(val) || "<span style='color:#666;'>No notes yet.</span>";
                    notesEdit.style.display = "none";
                    notesDisplay.style.display = "";
                    notesToggle.textContent = "Edit";
                } else {
                    notesDisplay.style.display = "none";
                    notesEdit.style.display = "";
                    notesToggle.textContent = "Save";
                    notesEdit.focus();
                }
            });
        }

        // Fill risers/fallers counts if present
        if (status.risers != null) {
            const el = document.getElementById("dash-risers");
            if (el) el.textContent = status.risers;
        }
        if (status.fallers != null) {
            const el = document.getElementById("dash-fallers");
            if (el) el.textContent = status.fallers;
        }
    },

    // Refresh schema content (called on show and by auto-refresh)
    // Shows Column | Type | Latest and flashes individual cells that changed.
    async refreshSchema() {
        const el = document.getElementById("schema-content");
        const meta = document.getElementById("schema-meta");
        if (!el) return;

        try {
            const schemaRes = await fetch("/schema");
            if (!schemaRes.ok) {
                throw new Error(`HTTP ${schemaRes.status}`);
            }
            const schema = await schemaRes.json();

            if (meta && schema.db_size_mb != null) {
                meta.textContent = `(${schema.db_size_mb} MB)`;
            }

            // Store previous latest values so we can detect changes
            if (!this._prevLatest) this._prevLatest = {};

            let newHtml = "No tables found";
            const changedCells = []; // collect cells to flash after render

            if (schema.tables && Array.isArray(schema.tables) && schema.tables.length) {
                newHtml = schema.tables.map(t => {
                    const latest = t.latest || {};
                    const tableKey = t.table;
                    if (!this._prevLatest[tableKey]) this._prevLatest[tableKey] = {};

                    const cols = (t.columns || []).map(c => {
                        let val = latest[c.name];
                        const rawVal = val;
                        if (val == null) val = "—";
                        else if (typeof val === "number") val = val.toLocaleString();
                        else val = String(val).length > 60 ? String(val).slice(0, 57) + "…" : String(val);

                        const prev = this._prevLatest[tableKey][c.name];
                        const changed = prev !== undefined && String(prev) !== String(rawVal);
                        if (changed) {
                            changedCells.push(`${tableKey}::${c.name}`);
                        }
                        this._prevLatest[tableKey][c.name] = rawVal;

                        const cellId = `latest-${tableKey}-${c.name}`.replace(/[^a-zA-Z0-9_-]/g, "_");
                        return `
                            <tr>
                                <td style="padding:3px 12px 3px 0; color:#e0e0e0; white-space:nowrap; border-bottom:1px solid rgba(255,255,255,0.04);">${c.name || ""}</td>
                                <td style="padding:3px 12px 3px 0; color:#aaa; white-space:nowrap; border-bottom:1px solid rgba(255,255,255,0.04);">${c.type || "—"}</td>
                                <td id="${cellId}" style="padding:3px 0; color:#7fdbff; white-space:nowrap; border-bottom:1px solid rgba(255,255,255,0.04);">${this.escapeHtml(val)}</td>
                            </tr>
                        `;
                    }).join("");

                    return `
                        <div style="margin-bottom:14px; background:#0d1b2a; border:1px solid rgba(127,219,255,0.2); border-radius:6px; overflow:hidden;">
                            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 14px; background:rgba(127,219,255,0.08); border-bottom:1px solid rgba(127,219,255,0.15);">
                                <strong style="color:#7fdbff; font-size:0.95rem;">${t.table || ""}</strong>
                                <span style="color:#aaa; font-size:0.8rem;">${(t.rows || 0).toLocaleString()} rows</span>
                            </div>
                            <div style="padding:8px 14px 10px; overflow-x:auto;">
                                <table style="width:100%; border-collapse:collapse; font-size:0.82rem;">
                                    <thead>
                                        <tr>
                                            <th style="text-align:left; padding:4px 12px 4px 0; color:#7fdbff; width:200px; white-space:nowrap;">Column</th>
                                            <th style="text-align:left; padding:4px 12px 4px 0; color:#7fdbff; width:100px; white-space:nowrap;">Type</th>
                                            <th style="text-align:left; padding:4px 0; color:#7fdbff; white-space:nowrap;">Latest</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${cols}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    `;
                }).join("");
            }

            el.innerHTML = newHtml;

            // Flash only the cells that actually changed
            changedCells.forEach(key => {
                const [table, col] = key.split("::");
                const cellId = `latest-${table}-${col}`.replace(/[^a-zA-Z0-9_-]/g, "_");
                const cell = document.getElementById(cellId);
                if (cell) this.flashCell(cell);
            });

        } catch (e) {
            console.error("Schema refresh failed:", e);
            el.textContent = "Schema unavailable";
            if (meta) meta.textContent = "";
        }
    },

    // Flash a single cell (used for changed latest values)
    flashCell(cell) {
        if (!cell) return;
        cell.style.transition = "none";
        cell.style.backgroundColor = "rgba(127, 219, 255, 0.35)";
        cell.style.color = "#fff";
        setTimeout(() => {
            cell.style.transition = "background-color 1.6s ease-out, color 1.6s ease-out";
            cell.style.backgroundColor = "";
            cell.style.color = "#7fdbff";
        }, 50);
        setTimeout(() => {
            cell.style.transition = "";
        }, 1700);
    },

    formatDate(iso) {
        if (!iso) return "—";
        try {
            const d = new Date(iso);
            return d.toLocaleString("en-GB", { timeZone: "Europe/London" });
        } catch (e) {
            return iso;
        }
    },

    escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
};

// Hook into the global auto-refresh cycle so schema updates while Dashboard is visible
const originalRefreshVisible = window.refreshVisible;
window.refreshVisible = async function () {
    if (typeof originalRefreshVisible === "function") {
        await originalRefreshVisible();
    }
    // Refresh schema only when Dashboard is the current view
    if (window.AppState && window.AppState.currentTool === "dashboard" && window.Dashboard && typeof window.Dashboard.refreshSchema === "function") {
        window.Dashboard.refreshSchema();
    }
};