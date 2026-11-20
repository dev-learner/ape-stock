// static/js/dashboard.js
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
                    <p>ape-stock has evolved from a simple “buy the big fallers” tool into a decision-support system for discretionary dip-buying on pre-qualified names.</p>
                    <p>The Screener surfaces relatively stable, higher-quality FTSE names (trend + size). Persistence at the top of that list has shown strong historical edge. Tool 8 still shows the day’s movers so you can see dips inside the better names. Tool 3 tracks the positions you actually take, with charts and context.</p>
                    <p style="color:#fbbf24;"><strong>Note:</strong> The user is still learning. The strategy is shifting from mechanical dip-buying toward “buy success after serious analysis” — filters, persistence, news awareness, and live monitoring matter more than raw faller size.</p>
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

                <!-- Database Schema (live) -->
                <div class="card" id="schema-card">
                    <h3>Database Schema</h3>
                    <div class="section" id="schema-content" style="font-size:0.85rem; line-height:1.4;">
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

                <!-- Considerations -->
                <div class="card" style="grid-column:1 / -1;">
                    <h3>Considerations</h3>
                    <div class="section">
                    <strong>Filters & Scoring</strong>
                    <ul>
                        <li>Persistence ranking (top-N days) as live filter or score — strong edge in back-tests</li>
                        <li>Walk-forward ranking (no look-ahead) for realistic testing</li>
                        <li>Acceleration flag (3 m vs 6 m, optionally 1 m / 1 y)</li>
                        <li>Sector-relative strength deeper integration</li>
                        <li>Editable weights / thresholds in Tool 7 feeding both Screener and Hit</li>
                    </ul>
                    <strong>News, RNS & Alerts</strong>
                    <ul>
                        <li>News / RNS presence or negative-keyword flag on Screener and Tool 8</li>
                        <li>Alert system for open positions: price drop, MA loss, new RNS, rank drop, sector deterioration</li>
                        <li>Back-test impact of skipping entries with recent news</li>
                    </ul>
                    <strong>Data & Fundamentals</strong>
                    <ul>
                        <li>Deeper sector / industry analysis and relative performance</li>
                        <li>Expandable fundamentals row in Tool 3 (PE, yield, etc.)</li>
                        <li>Earnings-date proximity, ex-div awareness</li>
                    </ul>
                    <strong>UI & Workflow</strong>
                    <ul>
                        <li>Glossary / “How to read” / Help page</li>
                        <li>Drag-and-drop reordering in Tracker</li>
                        <li>Test-mode toggle (simulated data when market closed)</li>
                        <li>“Also down today” filter on Screener</li>
                        <li>Badge in Tool 8 for current Screener names</li>
                    </ul>
                    <strong>Process</strong>
                    <ul>
                        <li>User still learning — emphasis on analysis and monitoring over pure mechanical dip-buying</li>
                        <li>Discretionary exits expected to be earlier than fixed back-test stops</li>
                    </ul>
                    </div>
                </div>

            </div>
        `;

        // Live schema
        try {
            const schemaRes = await fetch("/schema");
            const schema = await schemaRes.json();
            const el = document.getElementById("schema-content");
            if (el && schema.tables) {
                el.innerHTML = schema.tables.map(t => {
                    const cols = t.columns.map(c => c.name).join(", ");
                    return `<strong>${t.table}</strong> (${t.rows} rows) — ${cols}`;
                }).join("<br>");
            }
        } catch (e) {
            const el = document.getElementById("schema-content");
            if (el) el.textContent = "Schema unavailable";
        }

        // Notes Edit / Save toggle
        const notesToggle = document.getElementById("notes-toggle");
        const notesDisplay = document.getElementById("notes-display");
        const notesEdit = document.getElementById("notes-edit");
        if (notesToggle && notesDisplay && notesEdit) {
            notesToggle.addEventListener("click", () => {
                const editing = notesEdit.style.display !== "none";
                if (editing) {
                    const text = notesEdit.value;
                    localStorage.setItem("dashboard_notes", text);
                    notesDisplay.innerHTML = this.escapeHtml(text) || "<span style='color:#666;'>No notes yet.</span>";
                    notesDisplay.style.display = "";
                    notesEdit.style.display = "none";
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
            const r = document.getElementById("dash-risers");
            if (r) r.textContent = status.risers;
        }
        if (status.fallers != null) {
            const f = document.getElementById("dash-fallers");
            if (f) f.textContent = status.fallers;
        }
    },

    formatDate(iso) {
        if (!iso) return "—";
        try {
            const d = new Date(iso);
            return d.toLocaleString("en-GB", { timeZone: "Europe/London" });
        } catch {
            return iso;
        }
    },

    escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }
};