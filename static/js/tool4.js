// static/js/tool4.js
window.Tool4 = {
    async show() {
        const res = await fetch("/screener");
        const data = await res.json();
        const rows = data.rows || [];

        // Gold star: symbols currently in Tool 8 risers or fallers
        let tool8Symbols = new Set();
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
            (result.risers || []).forEach(r => tool8Symbols.add(r.symbol));
            (result.fallers || []).forEach(r => tool8Symbols.add(r.symbol));
        } catch (e) {
            console.warn("Could not load Tool 8 symbols for stars", e);
        }
        window.AppState.tool8Symbols = tool8Symbols;

        this.render(rows);
    },

    render(rows) {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <h2>Screener (${rows.length} safe bets)</h2>
                <button id="add-to-tracker" class="mini-btn" style="background:#1e5c3a;">Add selected to Tracker</button>
            </div>
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        <th data-key="symbol" title="Ticker symbol">Symbol</th>
                        <th data-key="name" title="Company name">Name</th>
                        <th data-key="sector" title="Sector">Sector</th>
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
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => {
                        const star = window.AppState.tool8Symbols?.has(r.symbol) ? "⭐ " : "";
                        const dayCls = (r.change_pct || 0) >= 0 ? "positive" : "negative";
                        return `
                        <tr>
                            <td>${star}${r.symbol}</td>
                            <td>${(r.name || "").substring(0, 28)}</td>
                            <td>${r.sector || ""}</td>
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

        // Apply default sort: 3m % descending
        this.applyDefaultSort(table);
    },

    applyDefaultSort(table) {
        const th = table.querySelector('th[data-key="ret_3m"]');
        if (!th) return;
        // Simulate two clicks so it ends on descending (first click = asc, second = desc)
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
            // defaultTh.style.boxShadow = "";
        } else {
            defaultTh.style.background = "rgba(248, 113, 113, 0.25)";
            // defaultTh.style.boxShadow = "inset 0 0 0 2px #f87171";
        }
    },

    async refreshPrices() {
        try {
            const res = await fetch("/screener");
            const data = await res.json();
            const rows = data.rows || [];
            rows.forEach(r => {
                const priceCell = document.querySelector(`.price-cell[data-symbol="${r.symbol}"]`);
                const dayCell = document.querySelector(`.day-cell[data-symbol="${r.symbol}"]`);
                if (priceCell) priceCell.textContent = formatNumber(r.price);
                if (dayCell) {
                    dayCell.textContent = r.change_pct != null ? r.change_pct.toFixed(2) + "%" : "";
                    dayCell.className = `day-cell ${(r.change_pct || 0) >= 0 ? "positive" : "negative"}`;
                }
            });
        } catch (e) {}
    }
};