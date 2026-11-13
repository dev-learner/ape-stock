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

        container.innerHTML = `
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; padding:8px;">

                <!-- Overview -->
                <div class="card">
                    <h3>Ape-Stock Overview</h3>
                    <p>ape-stock has evolved from a simple “buy the big fallers” tool into a decision-support system for discretionary dip-buying on pre-qualified names.</p>
                    <p>The Screener surfaces relatively stable, higher-quality FTSE names (trend + size). Persistence at the top of that list has shown strong historical edge. Tool 8 still shows the day’s movers so you can see dips inside the better names. Tool 3 tracks the positions you actually take, with charts and context.</p>
                    <p style="color:#fbbf24;"><strong>Note:</strong> The user is still learning. The strategy is shifting from mechanical dip-buying toward “buy success after serious analysis” — filters, persistence, news awareness, and live monitoring matter more than raw faller size.</p>
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

                <!-- Database Schema -->
                <div class="card">
                    <h3>Database Schema</h3>
                    <div class="section" style="font-size:0.85rem; line-height:1.4;">
                    <strong>index_constituents</strong> — symbol, index_key<br>
                    <strong>index_quotes</strong> — price, change_pct, volume, avg_volume, name, sector, industry, market_cap, ret_3m, ret_6m, dist_52w_high, above_50ma, pct_from_50ma, above_200ma, pct_from_200ma, vol_20d, sector_rel_1d, sector_rel_5d, …<br>
                    <strong>daily_closes</strong> — symbol, date, close<br>
                    <strong>snapshots_5min</strong> — symbol, ts, price, …<br>
                    <strong>holdings</strong> / <strong>holdings_marks</strong> — positions and daily marks<br>
                    <strong>app_settings</strong> — key/value (incl. screener_metrics_updated)
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
                    UK timezone aware
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

        // Lightweight style injection if needed
        if (!document.getElementById("dash-card-style")) {
            const style = document.createElement("style");
            style.id = "dash-card-style";
            style.textContent = `
                .card { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
                        border-radius:8px; padding:14px 16px; }
                .card h3 { margin:0 0 10px 0; color:#7fdbff; font-size:1.05rem; }
                .section { margin-bottom:10px; font-size:0.9rem; line-height:1.45; }
                .section ul { margin:4px 0 0 18px; padding:0; }
                .section li { margin-bottom:3px; }
            `;
            document.head.appendChild(style);
        }

        // Fill Tool 8 counts if status provides them
        if (status.risers != null) {
            const el = document.getElementById("dash-risers");
            if (el) el.textContent = status.risers;
        }
        if (status.fallers != null) {
            const el = document.getElementById("dash-fallers");
            if (el) el.textContent = status.fallers;
        }
    },

    formatDate(iso) {
        if (!iso) return "—";
        try {
            const d = new Date(iso);
            const pad = n => String(n).padStart(2, "0");
            return `${pad(d.getDate())}:${pad(d.getMonth()+1)}:${d.getFullYear()} - ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
        } catch {
            return iso;
        }
    }
};