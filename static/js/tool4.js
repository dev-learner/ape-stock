// static/js/tool4.js
window.Tool4 = {
    fullRank: false,

    async show() {
        const url = this.fullRank ? "/screener?mode=full" : "/screener";
        const res = await fetch(url);
        const data = await res.json();
        const rows = data.rows || [];

        let tool8Risers = new Set();
        let tool8Fallers = new Set();
        try {
            const body = {
                risers_index: "ALL",
                fallers_index: "ALL",
                limit: "all"
            };
            const tres = await fetch("/tool/8", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            const tdata = await tres.json();
            const result = tdata.result || {};
            (result.risers || []).forEach(r => tool8Risers.add(r.symbol));
            (result.fallers || []).forEach(r => tool8Fallers.add(r.symbol));
        } catch (e) {
            console.warn("Could not load Tool 8 symbols", e);
        }
        window.AppState.tool8Risers = tool8Risers;
        window.AppState.tool8Fallers = tool8Fallers;

        this.render(rows);
    },

    render(rows) {
        const container = document.getElementById("results");
        const title = this.fullRank
            ? `Screener — Full Rank (${rows.length})`
            : `Screener (${rows.length} safe bets)`;
        const toggleLabel = this.fullRank ? "Optimal Rank" : "Full Rank";

        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h2>${title}</h2>
                <div>
                    <button id="rank-toggle" class="mini-btn" style="margin-right:8px; background:#1e3a5c;">${toggleLabel}</button>
                    <button id="show-candidates" class="mini-btn" style="margin-right:8px; background:#5c3a1e;">Show Candidates</button>
                    <button id="add-to-tracker" class="mini-btn" style="background:#1e5c3a;">Add selected to Tracker</button>
                </div>
            </div>
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        <th data-key="symbol" title="Ticker symbol">Symbol</th>
                        <th data-key="name" title="Company name">Name</th>
                        <th data-key="sector" title="Sector">Sector</th>
                        <th data-key="rank" title="Daily rank (1 = best)">Rank</th>
                        <th data-key="price" title="Latest price">Price</th>
                        <th data-key="change_pct" title="Today's percentage change">Day %</th>
                        <th data-key="ret_3m" title="3-month return">3m %</th>
                        <th data-key="ret_6m" title="6-month return">6m %</th>
                        <th data-key="dist_52w_high" title="Distance from 52-week high (0 = at the high)">Dist 52w</th>
                        <th data-key="pct_from_50ma" title="Percentage above/below 50-day MA">vs 50MA</th>
                        <th data-key="pct_from_200ma" title="Percentage above/below 200-day MA">vs 200MA</th>
                        <th data-key="vol_20d" title="20-day realised volatility">Vol 20d</th>
                        <th data-key="sector_rel_1d" title="1-day return relative to sector">Sec 1d</th>
                        <th data-key="sector_rel_5d" title="5-day return relative to sector">Sec 5d</th>
                        <th title="Candidate signal">Signal</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => {
                        let indicator = "";
                        if (window.AppState.tool8Risers?.has(r.symbol)) indicator = "🟢 ";
                        else if (window.AppState.tool8Fallers?.has(r.symbol)) indicator = "🔴 ";
                        const dayCls = (r.change_pct || 0) >= 0 ? "positive" : "negative";
                        return `
                        <tr>
                            <td>${indicator}${r.symbol}</td>
                            <td>${(r.name || "").substring(0, 28)}</td>
                            <td>${r.sector || ""}</td>
                            <td>${r.rank != null ? r.rank : ""}</td>
                            <td class="price-cell" data-symbol="${r.symbol}">${formatNumber(r.price)}</td>
                            <td class="day-cell ${dayCls}" data-symbol="${r.symbol}">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : ""}</td>
                            <td class="${(r.ret_3m || 0) >= 0 ? "positive" : "negative"}">${r.ret_3m != null ? r.ret_3m.toFixed(1) : ""}</td>
                            <td class="${(r.ret_6m || 0) >= 0 ? "positive" : "negative"}">${r.ret_6m != null ? r.ret_6m.toFixed(1) : ""}</td>
                            <td>${r.dist_52w_high != null ? r.dist_52w_high.toFixed(1) : ""}</td>
                            <td>${r.pct_from_50ma != null ? r.pct_from_50ma.toFixed(1) : ""}</td>
                            <td>${r.pct_from_200ma != null ? r.pct_from_200ma.toFixed(1) : ""}</td>
                            <td>${r.vol_20d != null ? r.vol_20d.toFixed(1) : ""}</td>
                            <td class="${(r.sector_rel_1d || 0) >= 0 ? "positive" : "negative"}">${r.sector_rel_1d != null ? r.sector_rel_1d.toFixed(1) : ""}</td>
                            <td class="${(r.sector_rel_5d || 0) >= 0 ? "positive" : "negative"}">${r.sector_rel_5d != null ? r.sector_rel_5d.toFixed(1) : ""}</td>
                            <td class="signal-cell"></td>
                            <td><input type="checkbox" data-symbol="${r.symbol}"></td>
                        </tr>`;
                    }).join("")}
                </tbody>
            </table>
        `;

        document.getElementById("rank-toggle")?.addEventListener("click", () => {
            this.fullRank = !this.fullRank;
            this.show();
        });

        document.getElementById("show-candidates")?.addEventListener("click", () => {
            const btn = document.getElementById("show-candidates");
            const isActive = btn.dataset.active === "true";
            const table = document.getElementById("screener-table");
            const trs = [...table.querySelectorAll("tbody tr")];

            // Read candidate settings (defaults match previous hard-coded rules)
            const rankCutoff = parseInt(localStorage.getItem("cand_rank") || "12", 10);
            const requireFaller = (localStorage.getItem("cand_require_faller") || "1") === "1";
            const vs50Buy = parseFloat(localStorage.getItem("cand_vs50_buy") || "0");
            const vs200Buy = parseFloat(localStorage.getItem("cand_vs200_buy") || "0");
            const vs50Hold = parseFloat(localStorage.getItem("cand_vs50_hold") || "0");
            const vs50Sell = parseFloat(localStorage.getItem("cand_vs50_sell") || "0");

            trs.forEach(tr => {
                const cells = tr.children;
                const rankText = cells[3].textContent.trim();
                const rank = rankText === "" ? NaN : parseInt(rankText, 10);
                const vs50 = parseFloat(cells[9].textContent);
                const vs200 = parseFloat(cells[10].textContent);
                const isFaller = cells[0].textContent.includes("🔴");

                let signal = "";
                if (!isNaN(rank) && rank <= rankCutoff &&
                    (!requireFaller || isFaller) &&
                    vs50 > vs50Buy && vs200 > vs200Buy) {
                    signal = "🟢 Buy";
                } else if (!isNaN(rank) && rank <= rankCutoff && vs50 >= vs50Hold) {
                    signal = "🟡 Hold";
                } else if (!isNaN(vs50) && vs50 < vs50Sell) {
                    signal = "🔴 Sell";
                }

                const sigCell = tr.querySelector(".signal-cell");
                if (sigCell) sigCell.textContent = isActive ? "" : signal;

                const keep = isActive || signal === "🟢 Buy" || signal === "🟡 Hold";
                tr.style.display = keep ? "" : "none";
            });

            btn.dataset.active = isActive ? "false" : "true";
            btn.textContent = isActive ? "Show Candidates" : "Show All";
        });

        document.getElementById("add-to-tracker")?.addEventListener("click", async () => {
            const checked = [...document.querySelectorAll("#screener-table input[type=checkbox]:checked")];
            if (!checked.length) return;

            const notional = parseFloat(localStorage.getItem("notional") || "500");
            const stamp = parseFloat(localStorage.getItem("stampPct") || "0.5");
            let added = 0;

            for (const cb of checked) {
                const sym = cb.dataset.symbol;
                const row = rows.find(r => r.symbol === sym);
                if (!row || row.price == null) continue;

                const res = await fetch("/holdings/open", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        symbol: sym,
                        price: row.price,
                        notional: notional,
                        stamp_pct: stamp
                    })
                });
                if (res.ok || res.status === 409) added++;
            }
            alert(`Processed ${added} name(s)`);
        });

        const table = document.getElementById("screener-table");
        if (window.makeTableSortable) {
            makeTableSortable(table, {
                onSort: (key, dir) => this.updateDefaultHighlight(key, dir)
            });
        }

        this.applyDefaultSort(table);
    },

    applyDefaultSort(table) {
        const th = table.querySelector('th[data-key="ret_3m"]');
        if (!th) return;
        th.click();
        th.click();
        this.updateDefaultHighlight("ret_3m", -1);
    },

    updateDefaultHighlight(key, dir) {
        const table = document.getElementById("screener-table");
        if (!table) return;
        const defaultTh = table.querySelector('th[data-key="ret_3m"]');
        if (!defaultTh) return;

        const isDefault = (key === "ret_3m" && dir === -1);
        if (isDefault) {
            defaultTh.style.background = "";
        } else {
            defaultTh.style.background = "rgba(248, 113, 113, 0.25)";
        }
    },

    async refreshPrices() {
        try {
            const url = this.fullRank ? "/screener?mode=full" : "/screener";
            const res = await fetch(url);
            const data = await res.json();
            const rows = data.rows || [];

            if (!window.lastPrices) window.lastPrices = {};

            rows.forEach(r => {
                const priceCell = document.querySelector(`.price-cell[data-symbol="${r.symbol}"]`);
                const dayCell = document.querySelector(`.day-cell[data-symbol="${r.symbol}"]`);

                if (priceCell) {
                    const old = window.lastPrices[r.symbol];
                    const neu = r.price;
                    priceCell.textContent = formatNumber(neu);
                    if (old != null && neu != null && neu !== old) {
                        triggerFlash(priceCell, neu > old);
                    }
                    window.lastPrices[r.symbol] = neu;
                }

                if (dayCell) {
                    dayCell.textContent = r.change_pct != null ? r.change_pct.toFixed(2) + "%" : "";
                    dayCell.className = `day-cell ${(r.change_pct || 0) >= 0 ? "positive" : "negative"}`;
                }
            });
        } catch (e) {}
    }
};