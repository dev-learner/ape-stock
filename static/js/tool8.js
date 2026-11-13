// static/js/tool8.js
window.Tool8 = {
    async show(risersIndex, fallersIndex) {
        const body = {
            risers_index: risersIndex || window.AppState.currentRisersIndex || "ALL",
            fallers_index: fallersIndex || window.AppState.currentFallersIndex || "ALL",
            limit: parseInt(localStorage.getItem("listLimit") || "25", 10)
        };
        const res = await fetch("/tool/8", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        this.render(data.result || {});
    },

    render(result) {
        window.AppState.rawRisers = (result.risers || []).slice();
        window.AppState.rawFallers = (result.fallers || []).slice();
        window.AppState.currentRisersIndex = result.risers_index || "ALL";
        window.AppState.currentFallersIndex = result.fallers_index || "ALL";

        const risers = window.AppState.rawRisers;
        const fallers = window.AppState.rawFallers;

        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="split-view">
                <div class="split-panel">
                    <div class="region-bar">
                        <div class="left-controls"><h3>Risers (${risers.length})</h3><div class="region-buttons" id="risers-index-btns"></div></div>
                        <div class="right-controls">
                            <button class="mini-btn buy-btn" data-side="risers">Buy Selected</button>
                            <button class="mini-btn expand-btn" data-side="risers">Expand Selected</button>
                            <button class="mini-btn filter-btn" data-side="risers">Filter Selected</button>
                        </div>
                    </div>
                    <div id="risers-table"></div>
                </div>
                <div class="split-panel">
                    <div class="region-bar">
                        <div class="left-controls"><h3>Fallers (${fallers.length})</h3><div class="region-buttons" id="fallers-index-btns"></div></div>
                        <div class="right-controls">
                            <button class="mini-btn buy-btn" data-side="fallers">Buy Selected</button>
                            <button class="mini-btn expand-btn" data-side="fallers">Expand Selected</button>
                            <button class="mini-btn filter-btn" data-side="fallers">Filter Selected</button>
                        </div>
                    </div>
                    <div id="fallers-table"></div>
                </div>
            </div>`;

        this.buildIndexButtons("risers-index-btns", window.AppState.currentRisersIndex, "risers");
        this.buildIndexButtons("fallers-index-btns", window.AppState.currentFallersIndex, "fallers");
        this.renderFiltered("risers");
        this.renderFiltered("fallers");

        container.querySelectorAll(".expand-btn, .filter-btn, .save-btn").forEach(btn => {
            btn.replaceWith(btn.cloneNode(true));
        });

        container.querySelectorAll(".expand-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const side = btn.dataset.side;
                if (side === "risers") {
                    window.AppState.expandSelectedRisers = !window.AppState.expandSelectedRisers;
                } else {
                    window.AppState.expandSelectedFallers = !window.AppState.expandSelectedFallers;
                }
                btn.classList.toggle("active");
                this.renderFiltered(side);
            });
        });

        container.querySelectorAll(".filter-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const side = btn.dataset.side;
                if (side === "risers") window.AppState.filterSelectedRisers = !window.AppState.filterSelectedRisers;
                else window.AppState.filterSelectedFallers = !window.AppState.filterSelectedFallers;
                btn.classList.toggle("active");
                this.renderFiltered(side);
            });
        });

        container.querySelectorAll(".save-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const side = btn.dataset.side;
                const selected = side === "risers" ? window.AppState.selectedRisers : window.AppState.selectedFallers;
                const symbols = [...selected];
                if (!symbols.length) return;
                await fetch("/watchlist/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ symbols })
                });
                alert(`Added ${symbols.length} symbol(s) to watchlist`);
            });
        });

        container.querySelectorAll(".buy-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const side = btn.dataset.side;
                const selected = side === "risers" ? window.AppState.selectedRisers : window.AppState.selectedFallers;
                const raw = side === "risers" ? window.AppState.rawRisers : window.AppState.rawFallers;
                const notional = parseFloat(localStorage.getItem("notional") || "500");
                const stamp = parseFloat(localStorage.getItem("stampPct") || "0.5");

                if (!selected.size) return;

                const messages = [];
                for (const sym of selected) {
                    const row = raw.find(r => r.symbol === sym);
                    if (!row || !row.price) continue;

                    const res = await fetch("/holdings/open", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({
                            symbol: sym,
                            price: row.price,
                            notional: notional,
                            stamp_pct: stamp
                        })
                    });

                    let msgText = "Bought";
                    if (res.status === 409) {
                        msgText = "Already Bought";
                    } else if (!res.ok) {
                        msgText = "Failed";
                    }
                    messages.push(`${msgText}: ${sym}`);
                }

                for (let i = 0; i < messages.length; i++) {
                    setTimeout(() => {
                        let msg = document.getElementById("buy-msg");
                        if (!msg) {
                            msg = document.createElement("div");
                            msg.id = "buy-msg";
                            msg.style.cssText = `
                                position: fixed;
                                top: 20px;
                                right: 20px;
                                background: var(--accent);
                                color: white;
                                padding: 8px 16px;
                                border-radius: 4px;
                                opacity: 0;
                                transition: opacity 0.4s ease;
                                z-index: 9999;
                                pointer-events: none;
                            `;
                            document.body.appendChild(msg);
                        }
                        msg.textContent = messages[i];
                        msg.style.opacity = "1";
                        setTimeout(() => { msg.style.opacity = "0"; }, 1100);
                    }, i * 1300);
                }

                selected.clear();
                this.renderFiltered(side);
            });
        });
    },

    buildIndexButtons(containerId, active, side) {
        const el = document.getElementById(containerId);
        const INDEX_BUTTONS = ["100", "250", "ALL"];
        el.innerHTML = INDEX_BUTTONS.map(idx =>
            `<button class="mini-btn ${idx === active ? "active" : ""}" data-side="${side}" data-index="${idx}">${idx}</button>`
        ).join("");
        el.querySelectorAll(".mini-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const index = btn.dataset.index;
                el.querySelectorAll(".mini-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                if (side === "risers") {
                    window.AppState.currentRisersIndex = index;
                    this.show(index, window.AppState.currentFallersIndex);
                } else {
                    window.AppState.currentFallersIndex = index;
                    this.show(window.AppState.currentRisersIndex, index);
                }
            });
        });
    },

    renderFiltered(side) {
        const raw = side === "risers" ? window.AppState.rawRisers : window.AppState.rawFallers;
        if (!raw) return;
        const selected = side === "risers" ? window.AppState.selectedRisers : window.AppState.selectedFallers;
        const filterOn = side === "risers" ? window.AppState.filterSelectedRisers : window.AppState.filterSelectedFallers;
        const toShow = filterOn ? raw.filter(r => selected.has(r.symbol)) : raw.slice();
        const containerId = side === "risers" ? "risers-table" : "fallers-table";
        const indexKey = side === "risers" ? window.AppState.currentRisersIndex : window.AppState.currentFallersIndex;

        document.getElementById(containerId).innerHTML = this.renderTable(toShow, indexKey, side);

        const table = document.querySelector(`#${containerId} table`);
        if (table) makeTableSortable(table);
        attachCheckboxListeners(containerId, selected);

        document.querySelectorAll(`#${containerId} .vol-ratio`).forEach(async el => {
            const sym = el.dataset.symbol;
            const row = raw.find(x => x.symbol === sym);
            if (row && row.volume && row.avg_volume) {
                el.textContent = (row.volume / row.avg_volume).toFixed(1) + "×";
            } else {
                el.textContent = "—";
            }
        });
    },

    renderTable(rows, indexKey, side) {
        if (!rows || !rows.length) return `<p>No matching stocks in this index right now</p>`;
        const selected = side === "risers" ? window.AppState.selectedRisers : window.AppState.selectedFallers;
        const expandOn = side === "risers" ? window.AppState.expandSelectedRisers : window.AppState.expandSelectedFallers;

        const toShow = expandOn ? rows.filter(r => selected.has(r.symbol)) : rows;
        if (!toShow.length) return `<p>No selected stocks to expand</p>`;

        let html = `<table class="data-table"><thead><tr>
            <th data-key="symbol">Symbol</th>
            <th data-key="name">Name</th>
            <th data-key="price">Price</th>
            <th data-key="change">Change</th>
            <th data-key="change_pct">Change %</th>
            <th data-key="volume">Volume</th>
            <th data-key="hit">Hit</th>
            <th>Select</th>
        </tr></thead><tbody>`;

        for (const r of toShow) {
            const pct = r.change_pct != null ? r.change_pct.toFixed(2) + "%" : "";
            const cls = r.change_pct > 0 ? "positive" : r.change_pct < 0 ? "negative" : "";
            const checked = selected.has(r.symbol) ? "checked" : "";
            const shortName = (r.name || "").length > 15 ? (r.name || "").slice(0, 15) + "…" : (r.name || "");
            const fullName = (r.name || "").replace(/"/g, "&quot;");

            let points = 0;
            const possible = 4;
            const reasons = [];

            const fallersPct = parseFloat(localStorage.getItem("fallersSelectPct") || "5");
            const volRatioThreshold = parseFloat(localStorage.getItem("hitVolumeRatio") || "1.5");

            if (r.change_pct != null && Math.abs(r.change_pct) >= 5) {
                points++;
                reasons.push(`Change % ≥ 5% (${r.change_pct.toFixed(1)}%)`);
            }

            if (r.market_cap && r.change_pct != null) {
                const impact = Math.abs(r.market_cap * r.change_pct / 100);
                if (impact >= 20_000_000) {
                    points++;
                    reasons.push(`£ impact ≥ £20m (£${(impact/1e6).toFixed(1)}m)`);
                }
            }

            let volRatioVal = null;
            if (r.volume && r.avg_volume && r.avg_volume > 0) {
                volRatioVal = r.volume / r.avg_volume;
            }
            if (volRatioVal && volRatioVal >= volRatioThreshold) {
                points++;
                reasons.push(`Vol/Avg ≥ ${volRatioThreshold}× (${volRatioVal.toFixed(1)}×)`);
            }

            if (r.change_pct != null && r.change_pct <= -fallersPct && r.rsi7 != null && r.rsi7 <= 30) {
                points++;
                reasons.push(`RSI(7) ≤ 30 (${r.rsi7.toFixed(1)}) on faller`);
            }

            const hitPct = Math.round((points / possible) * 100);
            const hitCls = hitPct >= 75 ? "positive" : hitPct >= 50 ? "" : "negative";
            const hitTitle = reasons.length ? reasons.join("\n") : "No rules matched";
            const hitText = `${hitPct}%`;
            const highlight = hitPct >= 50 ? 'style="background:rgba(74,222,128,0.12)"' : "";

            html += `<tr class="main-row" data-symbol="${r.symbol}" ${highlight}>
                <td>${buildSymbolLink(r.symbol, indexKey)}</td>
                <td title="${fullName}">${shortName}</td>
                <td>${formatNumber(r.price, "price")}</td>
                <td class="${cls}">${formatNumber(r.change, "price")}</td>
                <td class="${cls}">${pct}</td>
                <td>${formatNumber(r.volume, "volume")}</td>
                <td class="${hitCls}" style="font-weight:bold;" title="${hitTitle.replace(/"/g, "&quot;")}">${hitText}</td>
                <td><input type="checkbox" data-symbol="${r.symbol}" data-side="${side}" ${checked}></td>
            </tr>`;

            if (expandOn && selected.has(r.symbol)) {
                const mktCap = r.market_cap ? "£" + (r.market_cap / 1e6).toFixed(1) + "m" : "—";
                const impactVal = (r.market_cap && r.change_pct != null)
                    ? (r.market_cap * r.change_pct / 100) : null;
                const impact = impactVal != null ? "£" + (impactVal / 1e6).toFixed(1) + "m" : "—";
                const sector = r.sector || "—";
                const industry = r.industry || "—";

                let volRatio = "—";
                if (r.volume && r.avg_volume) {
                    volRatio = (r.volume / r.avg_volume).toFixed(1) + "×";
                } else if (r.volume) {
                    volRatio = `<span class="vol-ratio" data-symbol="${r.symbol}">…</span>`;
                }

                html += `<tr class="details-row">
                    <td colspan="8" style="background:rgba(255,255,255,0.03); font-size:0.85rem; padding:8px 12px;">
                        <strong>Mkt cap:</strong> ${mktCap} &nbsp;·&nbsp;
                        <strong>£ impact:</strong> <span class="${impactVal >= 0 ? "positive" : "negative"}">${impact}</span> &nbsp;·&nbsp;
                        <strong>Vol/Avg:</strong> ${volRatio} &nbsp;·&nbsp;
                        <strong>Sector:</strong> ${sector} &nbsp;·&nbsp;
                        <strong>Industry:</strong> ${industry}
                    </td>
                </tr>`;
            }
        }
        html += "</tbody></table>";
        return html;
    },
};