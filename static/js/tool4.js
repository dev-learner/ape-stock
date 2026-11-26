// static/js/tool4.js
// Dual rank columns: Rank = base_rank, Rank # = active screener rank.

window.Tool4 = {
    mode: "base",

    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading…</div>`;

        if (this.mode === "ta") await this.showTA();
        else if (this.mode === "recovery") await this.showRecovery();
        else if (this.mode === "persistence") await this.showPersistence();
        else await this.showBase();
    },

    async showBase() {
        const res = await fetch("/screener?mode=base");
        const data = await res.json();
        this.render(data.rows || [], "Momentum 40% + Quality 30% + Valuation 20% + Liquidity 10%");
    },

    async showTA() {
        const res = await fetch("/screener?mode=ta");
        const data = await res.json();
        this.render(data.rows || [], "3m 25% + 6m 20% + vs 50MA 20% + vs 200MA 15% + Dist 52w 10% + Vol 20d 10%");
    },

    async showPersistence() {
        const res = await fetch("/screener?mode=full");
        const data = await res.json();
        this.render(data.rows || [], "Window 35d, Presence ≥50%, Rank ≤12");
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

        const criteria = `Lookback ${settings.rec_lookback_months || 12}m, Drawdown ≥${settings.rec_min_drawdown || 35}%, Bounce ≥${settings.rec_min_bounce || 15}%, Above 50MA: ${settings.rec_require_50ma !== "0" ? "Yes" : "No"}, MCap ≥£${settings.rec_min_mcap || 500}m`;

        if (!recoveryRows.length) {
            this.render([], criteria);
            return;
        }

        const taRes = await fetch("/screener?mode=base");
        const taData = await taRes.json();
        const taMap = {};
        (taData.rows || []).forEach(r => { taMap[r.symbol] = r; });

        const merged = recoveryRows.map((rec, idx) => {
            const ta = taMap[rec.symbol] || {};
            return {
                ...ta,
                symbol: rec.symbol,
                name: rec.name || ta.name,
                rank: idx + 1,
                base_rank: ta.base_rank,
                price: rec.current != null ? rec.current : ta.price
            };
        });

        this.render(merged, criteria);
    },

    render(rows, criteria) {
        const container = document.getElementById("results");
        const title = `Technical Analysis (${rows.length}) — <span style="font-size:0.75em; color:#aaa;">Selected on: ${criteria}</span>`;

        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:8px;">
                <h2 style="margin:0;">${title}</h2>
                <div style="display:flex; gap:8px; align-items:center;">
                    <select id="mode-select" class="mini-btn">
                        <option value="base" ${this.mode === "base" ? "selected" : ""}>Base</option>
                        <option value="ta" ${this.mode === "ta" ? "selected" : ""}>TA</option>
                        <option value="persistence" ${this.mode === "persistence" ? "selected" : ""}>Persistence</option>
                        <option value="recovery" ${this.mode === "recovery" ? "selected" : ""}>Recovery</option>
                    </select>
                    <button id="add-to-tracker" class="mini-btn" style="background:#1e5c3a;">Track!</button>
                </div>
            </div>
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
                        <th data-key="base_rank">Rank</th>
                        <th data-key="rank">Rank #</th>
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
                            <td>${r.base_rank ?? ""}</td>
                            <td>${r.rank ?? ""}</td>
                            <td>${formatNumber(r.price)}</td>
                            <td class="${dayCls}">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : ""}</td>
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
        if (window.makeTableSortable) makeTableSortable(document.getElementById("screener-table"));
    },

    bindControls(rows) {
        document.getElementById("mode-select")?.addEventListener("change", (e) => {
            this.mode = e.target.value;
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
                    body: JSON.stringify({ symbol: sym, price: row.price, notional, stamp_pct: stamp })
                });
                if (res.ok || res.status === 409) added++;
            }
            alert(`Processed ${added} name(s)`);
        });
    }
};