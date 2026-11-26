// static/js/tool4.js
// Tool 4 — Technical Analysis
// Persistence and Recovery modes. Live criteria shown in smaller font.

window.Tool4 = {
    fullRank: false,
    recoveryMode: false,

    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading…</div>`;

        if (this.recoveryMode) {
            await this.showRecovery();
        } else {
            await this.showPersistence();
        }
    },

    async showPersistence() {
        const url = this.fullRank ? "/screener?mode=full" : "/screener";
        const res = await fetch(url);
        const data = await res.json();
        const rows = data.rows || [];

        let tool8Risers = new Set();
        let tool8Fallers = new Set();
        try {
            const body = { risers_index: "ALL", fallers_index: "ALL", limit: "all" };
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

        const criteria = this.fullRank
            ? "Full universe"
            : "Window 35d, Presence ≥50%, Rank ≤12";
        this.renderPersistence(rows, criteria);
    },

    async showRecovery() {
        const recRes = await fetch("/screens/recovery");
        const recData = await recRes.json();
        const recoveryRows = recData.rows || [];

        let settings = {};
        try {
            const sRes = await fetch("/settings/get");
            settings = await sRes.json();
        } catch (e) {}

        const criteria = `Lookback ${settings.rec_lookback_months || 12}m, ` +
                         `Drawdown ≥${settings.rec_min_drawdown || 35}%, ` +
                         `Bounce ≥${settings.rec_min_bounce || 15}%, ` +
                         `Above 50MA: ${settings.rec_require_50ma !== "0" ? "Yes" : "No"}, ` +
                         `MCap ≥£${settings.rec_min_mcap || 500}m`;

        if (!recoveryRows.length) {
            this.renderRecovery([], criteria);
            return;
        }

        const taRes = await fetch("/screener?mode=full");
        const taData = await taRes.json();
        const taMap = {};
        (taData.rows || []).forEach(r => { taMap[r.symbol] = r; });

        const merged = recoveryRows.map((rec, idx) => {
            const ta = taMap[rec.symbol] || {};
            return {
                ...ta,
                symbol: rec.symbol,
                name: rec.name || ta.name,
                recovery_rank: idx + 1,
                price: rec.current != null ? rec.current : ta.price
            };
        });

        this.renderRecovery(merged, criteria);
    },

    renderPersistence(rows, criteria) {
        const container = document.getElementById("results");
        const title = `Technical Analysis — Persistence (${rows.length}) — <span style="font-size:0.75em; color:#aaa;">Selected on: ${criteria}</span>`;

        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:8px;">
                <h2 style="margin:0;">${title}</h2>
                <div style="display:flex; gap:8px;">
                    <button id="mode-toggle" class="mini-btn equal-width">${this.recoveryMode ? "Persistence" : "Recovery"}</button>
                    <button id="rank-toggle" class="mini-btn equal-width">${this.fullRank ? "Optimal Rank" : "Full Rank"}</button>
                    <button id="add-to-tracker" class="mini-btn equal-width" style="background:#1e5c3a;">Track!</button>
                </div>
            </div>
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
                        <th data-key="rank">Rank</th>
                        <th data-key="price">Price</th>
                        <th data-key="change_pct">Day %</th>
                        <th data-key="ret_3m">3m %</th>
                        <th data-key="ret_6m">6m %</th>
                        <th data-key="dist_52w_high">Dist 52w</th>
                        <th data-key="pct_from_50ma">vs 50MA</th>
                        <th data-key="pct_from_200ma">vs 200MA</th>
                        <th data-key="vol_20d">Vol 20d</th>
                        <th data-key="sector_rel_1d">Sec 1d</th>
                        <th data-key="sector_rel_5d">Sec 5d</th>
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
                            <td><input type="checkbox" data-symbol="${r.symbol}"></td>
                        </tr>`;
                    }).join("")}
                </tbody>
            </table>
        `;

        this.bindControls(rows);
        const table = document.getElementById("screener-table");
        if (window.makeTableSortable) {
            makeTableSortable(table, { onSort: (key, dir) => this.updateDefaultHighlight(key, dir) });
        }
        this.applyDefaultSort(table);
    },

    renderRecovery(rows, criteria) {
        const container = document.getElementById("results");
        const title = `Technical Analysis — Recovery (${rows.length}) — <span style="font-size:0.75em; color:#aaa;">Selected on: ${criteria}</span>`;

        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:8px;">
                <h2 style="margin:0;">${title}</h2>
                <div style="display:flex; gap:8px;">
                    <button id="mode-toggle" class="mini-btn equal-width">${this.recoveryMode ? "Persistence" : "Recovery"}</button>
                    <button id="rank-toggle" class="mini-btn equal-width">${this.fullRank ? "Optimal Rank" : "Full Rank"}</button>
                    <button id="add-to-tracker" class="mini-btn equal-width" style="background:#1e5c3a;">Track!</button>
                </div>
            </div>
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
                        <th data-key="rank" title="Recovery rank">Rank</th>
                        <th data-key="price">Price</th>
                        <th data-key="change_pct">Day %</th>
                        <th data-key="ret_3m">3m %</th>
                        <th data-key="ret_6m">6m %</th>
                        <th data-key="dist_52w_high">Dist 52w</th>
                        <th data-key="pct_from_50ma">vs 50MA</th>
                        <th data-key="pct_from_200ma">vs 200MA</th>
                        <th data-key="vol_20d">Vol 20d</th>
                        <th data-key="sector_rel_1d">Sec 1d</th>
                        <th data-key="sector_rel_5d">Sec 5d</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => {
                        const dayCls = (r.change_pct || 0) >= 0 ? "positive" : "negative";
                        return `
                        <tr>
                            <td>${r.symbol}</td>
                            <td>${(r.name || "").substring(0, 28)}</td>
                            <td>${r.sector || ""}</td>
                            <td>${r.recovery_rank ?? ""}</td>
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
                            <td><input type="checkbox" data-symbol="${r.symbol}"></td>
                        </tr>`;
                    }).join("") || `<tr><td colspan="15" style="text-align:center; color:#666;">No recovery candidates.</td></tr>`}
                </tbody>
            </table>
        `;

        this.bindControls(rows);
        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("screener-table"));
        }
    },

    bindControls(rows) {
        document.getElementById("mode-toggle")?.addEventListener("click", () => {
            this.recoveryMode = !this.recoveryMode;
            this.show();
        });
        document.getElementById("rank-toggle")?.addEventListener("click", () => {
            this.fullRank = !this.fullRank;
            this.show();
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
        defaultTh.style.background = isDefault ? "" : "rgba(248, 113, 113, 0.25)";
    },

    async refreshPrices() {
        if (this.recoveryMode || window.AppState.currentTool !== "4") return;
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
                    if (old != null && neu != null && neu !== old) triggerFlash(priceCell, neu > old);
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