// static/js/tool4.js
window.Tool4 = {
    async show() {
        const res = await fetch("/screener");
        const data = await res.json();
        this.render(data.rows || []);
    },

    render(rows) {
        const container = document.getElementById("results");
        let html = `
            <div class="region-bar">
                <h3>Screener (${rows.length} safe bets)</h3>
                <div class="right-controls">
                    <button class="mini-btn" id="add-selected" style="background:#1e5c3a;">Add selected to Tracker</button>
                </div>
            </div>
            <table class="data-table" id="screener-table">
                <thead><tr>
                    <th data-key="symbol">Symbol</th>
                    <th data-key="name">Name</th>
                    <th data-key="sector">Sector</th>
                    <th data-key="price" title="Latest price from index_quotes">Price</th>
                    <th data-key="change_pct" title="Today’s percentage change">Day %</th>
                    <th data-key="ret_3m" title="3-month price return. Slow-moving trend measure. Positive = up over the last ~63 trading days.">3m %</th>
                    <th data-key="ret_6m" title="6-month price return. Longer trend context. Positive = up over the last ~126 trading days.">6m %</th>
                    <th data-key="dist_52w_high" title="Distance from 52-week high. 0 = at the high. Negative = below it. Shows how extended the name is versus its recent peak.">Dist 52w</th>
                    <th data-key="pct_from_50ma" title="% distance from the 50-day moving average. Positive / green = price is above the 50-day MA (shorter-term uptrend).">vs 50MA</th>
                    <th data-key="pct_from_200ma" title="% distance from the 200-day moving average. Positive / green = price is above the 200-day MA (longer-term uptrend).">vs 200MA</th>
                    <th data-key="vol_20d" title="20-day realised volatility (std dev of daily returns). Higher = more volatile / larger typical daily moves.">Vol 20d</th>
                    <th data-key="sector_rel_1d" title="Today’s return minus the average return of its sector. Positive = outperforming its sector today.">Sec 1d</th>
                    <th data-key="sector_rel_5d" title="5-day return minus the average 5-day return of its sector. Positive = outperforming its sector over the last week.">Sec 5d</th>
                    <th><input type="checkbox" id="select-all" title="Select / deselect all"></th>
                </tr></thead><tbody>`;

        rows.forEach(r => {
            const cls3 = r.ret_3m >= 0 ? "positive" : "negative";
            const cls6 = r.ret_6m >= 0 ? "positive" : "negative";
            const clsDist = r.dist_52w_high >= -5 ? "positive" : "";
            const cls50 = r.above_50ma ? "positive" : "negative";
            const cls200 = r.above_200ma ? "positive" : "negative";
            const clsSec1 = r.sector_rel_1d >= 0 ? "positive" : "negative";
            const clsSec5 = r.sector_rel_5d >= 0 ? "positive" : "negative";
            const clsDay = r.change_pct > 0 ? "positive" : r.change_pct < 0 ? "negative" : "";

            html += `<tr data-symbol="${r.symbol}">
                <td>${r.symbol}</td>
                <td>${(r.name || "").substring(0, 28)}</td>
                <td>${r.sector || "—"}</td>
                <td class="price-cell">${formatNumber(r.price, "price")}</td>
                <td class="day-cell ${clsDay}">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : "—"}</td>
                <td class="${cls3}">${r.ret_3m != null ? r.ret_3m.toFixed(1) : "—"}</td>
                <td class="${cls6}">${r.ret_6m != null ? r.ret_6m.toFixed(1) : "—"}</td>
                <td class="${clsDist}">${r.dist_52w_high != null ? r.dist_52w_high.toFixed(1) : "—"}</td>
                <td class="${cls50}">${r.pct_from_50ma != null ? r.pct_from_50ma.toFixed(1) : "—"}</td>
                <td class="${cls200}">${r.pct_from_200ma != null ? r.pct_from_200ma.toFixed(1) : "—"}</td>
                <td>${r.vol_20d != null ? r.vol_20d.toFixed(1) : "—"}</td>
                <td class="${clsSec1}">${r.sector_rel_1d != null ? r.sector_rel_1d.toFixed(1) : "—"}</td>
                <td class="${clsSec5}">${r.sector_rel_5d != null ? r.sector_rel_5d.toFixed(1) : "—"}</td>
                <td><input type="checkbox" class="row-select" data-symbol="${r.symbol}" data-price="${r.price || ""}"></td>
            </tr>`;
        });
        html += `</tbody></table>`;
        if (!rows.length) {
            html += `<p style="padding:16px; color:#888;">No names currently match the safe-bet filters.</p>`;
        }
        container.innerHTML = html;

        const selectAll = document.getElementById("select-all");
        if (selectAll) {
            selectAll.addEventListener("change", () => {
                container.querySelectorAll(".row-select").forEach(cb => cb.checked = selectAll.checked);
            });
        }

        const addBtn = document.getElementById("add-selected");
        if (addBtn) {
            addBtn.addEventListener("click", async () => {
                const selected = [...container.querySelectorAll(".row-select:checked")];
                if (!selected.length) return;
                const notional = parseFloat(localStorage.getItem("notional") || "500");
                const stamp = parseFloat(localStorage.getItem("stampPct") || "0.5");
                for (const cb of selected) {
                    const sym = cb.dataset.symbol;
                    const price = parseFloat(cb.dataset.price);
                    if (!sym || isNaN(price)) continue;
                    const res = await fetch("/holdings/open", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({ symbol: sym, price, notional, stamp_pct: stamp })
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
                    setTimeout(() => { msg.style.opacity = "0"; }, 1000);
                }
            });
        }

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("screener-table"));
        }
    },

    async refreshPrices() {
        if (window.AppState.currentTool !== "4") return;
        try {
            const res = await fetch("/screener");
            const data = await res.json();
            const rows = data.rows || [];
            rows.forEach(r => {
                const tr = document.querySelector(`#screener-table tr[data-symbol="${r.symbol}"]`);
                if (!tr) return;
                const priceCell = tr.querySelector(".price-cell");
                const dayCell = tr.querySelector(".day-cell");
                if (priceCell) priceCell.textContent = formatNumber(r.price, "price");
                if (dayCell) {
                    const cls = r.change_pct > 0 ? "positive" : r.change_pct < 0 ? "negative" : "";
                    dayCell.className = `day-cell ${cls}`;
                    dayCell.textContent = r.change_pct != null ? r.change_pct.toFixed(2) + "%" : "—";
                }
                // keep checkbox data-price fresh
                const cb = tr.querySelector(".row-select");
                if (cb) cb.dataset.price = r.price || "";
            });
        } catch (e) {
            console.warn("Screener price refresh failed", e);
        }
    }
};