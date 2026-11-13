// static/js/tool3.js
window.Tool3 = {
    async show() {
        const res = await fetch("/holdings/list");
        const rows = await res.json();
        this.render(rows);
    },

    render(rows) {
        const container = document.getElementById("results");
        let html = `
            <div class="region-bar">
                <h3>Holdings Tracker (${rows.length} open)</h3>
                <div class="right-controls">
                    <button class="mini-btn" id="search-add">Search</button>
                    <button class="mini-btn" id="reset-holdings" style="background:#c0392b; border-color:#c0392b; color:white;">Reset Holdings</button>
                </div>
            </div>
            <table class="data-table" id="holdings-table">
                <thead><tr>
                    <th>No.</th><th>Date</th><th>Symbol</th><th>Price Added</th><th>Current</th>
                    ${Array.from({length:14}, (_,i) => `<th>+D${i+1}</th>`).join("")}
                    <th>Net £</th><th></th>
                </tr></thead><tbody>`;

        rows.forEach((h, idx) => {
            const marks = {};
            (h.marks || []).forEach(m => marks[m.day_offset] = m);

            let current = h.entry_price;
            let maxOffset = -1;
            for (const m of (h.marks || [])) {
                if (m.day_offset > maxOffset) {
                    maxOffset = m.day_offset;
                    current = m.price;
                }
            }

            let net = 0;
            if (h.shares && current) {
                net = (h.shares * current) - h.notional;
            }
            const netCls = net >= 0 ? "positive" : "negative";

            html += `<tr data-id="${h.id}" class="main-row">
                <td>${idx+1}</td>
                <td>${h.entry_date}</td>
                <td>${h.symbol}</td>
                <td>${formatNumber(h.entry_price,"price")}</td>
                <td>${formatNumber(current,"price")}</td>`;

            for (let d = 1; d <= 14; d++) {
                const m = marks[d];
                if (m && m.price != null) {
                    const delta = m.price - h.entry_price;
                    const cls = delta >= 0 ? "positive" : "negative";
                    const sign = delta >= 0 ? "+" : "";
                    html += `<td class="${cls}">${sign}${formatNumber(delta,"price")}</td>`;
                } else {
                    html += `<td>—</td>`;
                }
            }
            html += `<td class="${netCls}">${formatNumber(net,"price")}</td>
                     <td><button class="mini-btn sell-btn" data-id="${h.id}" data-price="${current}">Sell</button></td>
                     </tr>`;

            const dayChange = h.change != null ? formatNumber(h.change, "price") : "—";
            const dayPct = h.change_pct != null ? h.change_pct.toFixed(2) + "%" : "—";
            const dayCls = h.change_pct > 0 ? "positive" : h.change_pct < 0 ? "negative" : "";
            const vol = h.volume != null ? formatNumber(h.volume, "volume") : "—";

            html += `<tr class="details-row" data-id="${h.id}">
                <td colspan="20" style="background:rgba(255,255,255,0.03); padding:12px 16px;">
                    <div style="display:flex; gap:16px; align-items:flex-start;">
                        <!-- Fixed-width info block so charts always start at the same horizontal position -->
                        <div style="width:220px; min-width:220px; padding-top:8px; flex-shrink:0;">
                            <strong>${h.name || h.symbol}</strong><br>
                            <span style="color:var(--accent);">${h.exchange || "—"}</span><br>
                            Day: <span class="${dayCls}">${dayChange} (${dayPct})</span><br>
                            Vol: ${vol}
                        </div>
                        <!-- Charts start here — roughly under the Current column -->
                        <div style="display:flex; gap:20px; align-items:flex-end; margin-left:40px;">
                            <div style="text-align:center;">
                                <div style="font-size:0.75rem; color:var(--accent); margin-bottom:4px; height:16px;">90-day 5-min</div>
                                <canvas class="chart-multi" data-symbol="${h.symbol}" width="200" height="90" style="background:rgba(0,0,0,0.2); border-radius:4px; display:block;"></canvas>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:0.75rem; color:var(--accent); margin-bottom:4px; height:16px;">Today 5-min</div>
                                <canvas class="chart-5min" data-symbol="${h.symbol}" width="200" height="90" style="background:rgba(0,0,0,0.2); border-radius:4px; display:block;"></canvas>
                            </div>
                            <div style="text-align:center;">
                                <div style="font-size:0.75rem; color:var(--accent); margin-bottom:4px; height:16px;">14-day progress</div>
                                <canvas class="chart-daily" data-id="${h.id}" width="200" height="90" style="background:rgba(0,0,0,0.2); border-radius:4px; display:block;"></canvas>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>`;
        });
        html += `</tbody></table>`;
        container.innerHTML = html;

        const resetBtn = document.getElementById("reset-holdings");
        if (resetBtn) {
            resetBtn.addEventListener("click", async () => {
                if (!confirm("Clear ALL holdings data (open + history)?")) return;
                await fetch("/holdings/reset", { method: "POST" });
                this.show();
            });
        }

        const searchBtn = document.getElementById("search-add");
        if (searchBtn) {
            searchBtn.addEventListener("click", () => this.openSearch());
        }

        container.querySelectorAll(".sell-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.dataset.id;
                const price = parseFloat(btn.dataset.price);
                if (!id || isNaN(price)) return;
                await fetch("/holdings/close", {
                    method: "POST",
                    headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({id, exit_price: price, reason: "manual"})
                });
                this.show();
            });
        });

        requestAnimationFrame(() => this.drawCharts(rows));
    },

    openSearch() {
        let modal = document.getElementById("search-modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.id = "search-modal";
            modal.style.cssText = `
                position: fixed; inset: 0; background: rgba(0,0,0,0.65);
                display: flex; align-items: center; justify-content: center; z-index: 10000;
            `;
            modal.innerHTML = `
                <div style="background:#0d1b2a; padding:24px; border-radius:8px; min-width:380px; border:1px solid #1e3a5f; box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                    <h3 style="margin:0 0 16px 0; color:#7fdbff;">Add to Tracker</h3>
                    <input id="search-input" type="text" placeholder="Symbol or name (e.g. BP or BP.L)" 
                           style="width:100%; padding:10px 12px; margin-bottom:12px; background:#1a1a2e; color:white; 
                                  border:1px solid #1e3a5f; border-radius:4px; font-size:0.95rem;">
                    <div id="search-results" style="max-height:240px; overflow:auto; margin-bottom:16px; border:1px solid #1e3a5f; border-radius:4px;"></div>
                    <div style="display:flex; gap:8px; justify-content:flex-end;">
                        <button class="mini-btn" id="search-cancel">Cancel</button>
                        <button class="mini-btn" id="search-confirm" style="background:#1e5c3a;">Add</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        modal.style.display = "flex";
        const input = document.getElementById("search-input");
        input.value = "";
        input.dataset.price = "";
        input.focus();
        document.getElementById("search-results").innerHTML = "";

        const doSearch = async () => {
            const q = input.value.trim();
            if (q.length < 1) {
                document.getElementById("search-results").innerHTML = "";
                return;
            }
            const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            const box = document.getElementById("search-results");
            if (!data.length) {
                box.innerHTML = "<p style='color:#888; padding:8px; margin:0;'>No matches</p>";
                return;
            }
            box.innerHTML = data.slice(0, 10).map(r =>
                `<div class="search-hit" data-symbol="${r.symbol}" data-price="${r.price || ""}" 
                      style="padding:8px 12px; cursor:pointer; border-bottom:1px solid #1e3a5f; color:#e0e0e0;">
                    <strong>${r.symbol}</strong> — ${r.name || ""} 
                    ${r.price ? `<span style="float:right; color:#7fdbff;">${formatNumber(r.price, "price")}</span>` : ""}
                </div>`
            ).join("");
            box.querySelectorAll(".search-hit").forEach(el => {
                el.addEventListener("click", () => {
                    input.value = el.dataset.symbol;
                    input.dataset.price = el.dataset.price;
                    box.querySelectorAll(".search-hit").forEach(h => h.style.background = "");
                    el.style.background = "rgba(127,219,255,0.15)";
                });
                el.addEventListener("mouseenter", () => {
                    if (el.style.background === "") el.style.background = "rgba(255,255,255,0.05)";
                });
                el.addEventListener("mouseleave", () => {
                    if (!el.style.background.includes("127,219,255")) el.style.background = "";
                });
            });
        };

        input.oninput = doSearch;
        input.onkeydown = (e) => { if (e.key === "Enter") doSearch(); };

        document.getElementById("search-cancel").onclick = () => { modal.style.display = "none"; };

        document.getElementById("search-confirm").onclick = async () => {
            const sym = input.value.trim().toUpperCase();
            const price = parseFloat(input.dataset.price);
            if (!sym || isNaN(price)) {
                alert("Select a symbol with a price from the list");
                return;
            }
            const notional = parseFloat(localStorage.getItem("notional") || "500");
            const stamp = parseFloat(localStorage.getItem("stampPct") || "0.5");
            const res = await fetch("/holdings/open", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ symbol: sym, price: price, notional: notional, stamp_pct: stamp })
            });
            let msgText = "Bought";
            if (res.status === 409) msgText = "Already Bought";
            else if (!res.ok) msgText = "Failed";

            let msg = document.getElementById("buy-msg");
            if (!msg) {
                msg = document.createElement("div");
                msg.id = "buy-msg";
                msg.style.cssText = `
                    position: fixed; top: 20px; right: 20px; background: var(--accent);
                    color: white; padding: 8px 16px; border-radius: 4px; opacity: 0;
                    transition: opacity 0.4s ease; z-index: 9999; pointer-events: none;
                `;
                document.body.appendChild(msg);
            }
            msg.textContent = `${msgText}: ${sym}`;
            msg.style.opacity = "1";
            setTimeout(() => { msg.style.opacity = "0"; }, 1200);

            input.value = "";
            input.dataset.price = "";
            document.getElementById("search-results").innerHTML = "";
            input.focus();
            if (res.ok) this.show();
        };
    },

    async drawCharts(rows) {
        // Multi-day 5-min (last ~90 days)
        document.querySelectorAll("canvas.chart-multi").forEach(async canvas => {
            const sym = canvas.dataset.symbol;
            try {
                const res = await fetch(`/sparkline/${sym}?days=90`);
                const data = await res.json();
                const prices = (data.prices && data.prices.length > 1) ? data.prices : [1, 1];
                drawSparkline(canvas, prices, "line");
            } catch (e) {
                drawSparkline(canvas, [1, 1], "line");
            }
        });

        // Today 5-min
        document.querySelectorAll("canvas.chart-5min").forEach(async canvas => {
            const sym = canvas.dataset.symbol;
            try {
                const res = await fetch(`/sparkline/${sym}`);
                const data = await res.json();
                const prices = (data.prices && data.prices.length > 1) ? data.prices : [1, 1];
                drawSparkline(canvas, prices, "line");
            } catch (e) {
                drawSparkline(canvas, [1, 1], "line");
            }
        });

        // 14-day progress from marks
        rows.forEach(h => {
            const canvas = document.querySelector(`canvas.chart-daily[data-id="${h.id}"]`);
            if (!canvas) return;
            const prices = [h.entry_price];
            const marks = (h.marks || []).slice().sort((a, b) => a.day_offset - b.day_offset);
            marks.forEach(m => {
                if (m.day_offset >= 1 && m.price != null) prices.push(m.price);
            });
            if (prices.length < 2) prices.push(h.entry_price);
            drawSparkline(canvas, prices, "line");
        });
    }
};