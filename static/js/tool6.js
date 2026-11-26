// static/js/tool6.js
// Tool 6 — Fundamentals
// All view: sequential # + "Descending Mkt. Cap." in smaller font.
// Recovery view: live criteria in smaller font + Recovery rank.

window.Tool6 = {
    recoveryMode: false,

    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading…</div>`;

        if (this.recoveryMode) {
            await this.showRecovery();
        } else {
            await this.showAll();
        }
    },

    async showAll() {
        const res = await fetch("/fundamentals");
        const data = await res.json();
        const rows = (data.rows || []).sort((a, b) => (b.market_cap || 0) - (a.market_cap || 0));
        this.render(rows, false, "Descending Mkt. Cap.");
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
            this.render([], true, criteria);
            return;
        }

        const fundRes = await fetch("/fundamentals");
        const fundData = await fundRes.json();
        const fundMap = {};
        (fundData.rows || []).forEach(r => { fundMap[r.symbol] = r; });

        const merged = recoveryRows.map((rec, idx) => {
            const fund = fundMap[rec.symbol] || {};
            return {
                ...fund,
                symbol: rec.symbol,
                name: rec.name || fund.name,
                recovery_rank: idx + 1
            };
        });

        this.render(merged, true, criteria);
    },

    render(rows, isRecovery, criteria) {
        const container = document.getElementById("results");
        const title = `Fundamentals${isRecovery ? " — Recovery" : ""} (${rows.length}) — <span style="font-size:0.75em; color:#aaa;">Selected on: ${criteria}</span>`;

        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap:8px;">
                <h2 style="margin:0;">${title}</h2>
                <div style="display:flex; gap:8px;">
                    <button id="mode-toggle" class="mini-btn equal-width">${this.recoveryMode ? "All" : "Recovery"}</button>
                    <button id="add-to-tracker" class="mini-btn equal-width" style="background:#1e5c3a;">Track!</button>
                </div>
            </div>
            <table class="data-table" id="fund-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
                        <th data-key="rank">${isRecovery ? "Rank" : "#"}</th>
                        <th data-key="market_cap">Market Cap</th>
                        <th data-key="pe_trailing">Trailing PE</th>
                        <th data-key="pe_forward">Forward PE</th>
                        <th data-key="price_to_book">P/B</th>
                        <th data-key="dividend_yield">Div Yield</th>
                        <th data-key="roe">ROE</th>
                        <th data-key="profit_margin">Profit Margin</th>
                        <th data-key="revenue_growth">Rev Growth</th>
                        <th data-key="beta">Beta</th>
                        <th data-key="current_ratio">Current Ratio</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((r, idx) => `
                        <tr>
                            <td>${r.symbol}</td>
                            <td>${(r.name || "").substring(0, 28)}</td>
                            <td>${r.sector || ""}</td>
                            <td>${isRecovery ? (r.recovery_rank ?? "") : (idx + 1)}</td>
                            <td>${r.market_cap ? (r.market_cap / 1e9).toFixed(2) + "bn" : ""}</td>
                            <td>${r.pe_trailing != null ? r.pe_trailing.toFixed(1) : ""}</td>
                            <td>${r.pe_forward != null ? r.pe_forward.toFixed(1) : ""}</td>
                            <td>${r.price_to_book != null ? r.price_to_book.toFixed(2) : ""}</td>
                            <td>${r.dividend_yield != null ? r.dividend_yield.toFixed(2) + "%" : ""}</td>
                            <td>${r.roe != null ? (r.roe * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.profit_margin != null ? (r.profit_margin * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.revenue_growth != null ? (r.revenue_growth * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.beta != null ? r.beta.toFixed(2) : ""}</td>
                            <td>${r.current_ratio != null ? r.current_ratio.toFixed(2) : ""}</td>
                            <td><input type="checkbox" data-symbol="${r.symbol}"></td>
                        </tr>`).join("") || `<tr><td colspan="15" style="text-align:center; color:#666;">No data.</td></tr>`}
                </tbody>
            </table>
        `;

        this.bindControls(rows);
        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("fund-table"));
        }
    },

    bindControls(rows) {
        document.getElementById("mode-toggle")?.addEventListener("click", () => {
            this.recoveryMode = !this.recoveryMode;
            this.show();
        });

        document.getElementById("add-to-tracker")?.addEventListener("click", async () => {
            const checked = [...document.querySelectorAll("#fund-table input[type=checkbox]:checked")];
            if (!checked.length) return;

            const notional = parseFloat(localStorage.getItem("notional") || "500");
            const stamp = parseFloat(localStorage.getItem("stampPct") || "0.5");
            let added = 0;

            for (const cb of checked) {
                const sym = cb.dataset.symbol;
                const priceRes = await fetch(`/quote/${sym}`);
                const priceData = await priceRes.json();
                const price = priceData.price;
                if (price == null) continue;

                const res = await fetch("/holdings/open", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        symbol: sym,
                        price: price,
                        notional: notional,
                        stamp_pct: stamp
                    })
                });
                if (res.ok || res.status === 409) added++;
            }
            alert(`Processed ${added} name(s)`);
        });
    }
};