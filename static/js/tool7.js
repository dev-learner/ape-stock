// static/js/tool7.js
window.Tool7 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:12px; color:#aaa;">Loading candidates…</div>`;

        try {
            const [screenerRes, fundRes, settingsRes] = await Promise.all([
                fetch("/screener").then(r => r.json()),
                fetch("/fundamentals").then(r => r.json()),
                fetch("/settings/get").then(r => r.json())
            ]);

            const screener = screenerRes.rows || [];
            const fundamentals = fundRes.rows || fundRes || [];
            const s = settingsRes || {};

            const rankMax = parseInt(s.cand_rank_max || "12", 10);
            const peMin = parseFloat(s.cand_pe_min || "5");
            const peMax = parseFloat(s.cand_pe_max || "40");
            const pbMax = parseFloat(s.cand_pb_max || "4");
            const requireDiv = (s.cand_require_div === "1");

            const fundMap = {};
            fundamentals.forEach(f => { fundMap[f.symbol] = f; });

            const candidates = screener
                .filter(r => {
                    const rank = parseInt(r.rank, 10);
                    if (isNaN(rank) || rank > rankMax) return false;

                    const f = fundMap[r.symbol] || {};
                    const pe = parseFloat(f.pe_trailing);
                    const pb = parseFloat(f.price_to_book);
                    const div = parseFloat(f.dividend_yield);

                    if (!isNaN(pe) && (pe < peMin || pe > peMax)) return false;
                    if (!isNaN(pb) && pb >= pbMax) return false;
                    if (requireDiv && (isNaN(div) || div <= 0)) return false;

                    return true;
                })
                .sort((a, b) => (parseInt(a.rank) || 999) - (parseInt(b.rank) || 999));

            this.render(container, candidates, fundMap, rankMax, peMin, peMax, pbMax, requireDiv);
        } catch (e) {
            container.innerHTML = `<div style="padding:12px; color:#f87171;">Failed to load candidates.</div>`;
        }
    },

    render(container, rows, fundMap, rankMax, peMin, peMax, pbMax, requireDiv) {
        const body = rows.map(r => {
            const f = fundMap[r.symbol] || {};
            return `
                <tr>
                    <td>${r.symbol}</td>
                    <td>${r.name || ""}</td>
                    <td>${r.sector || ""}</td>
                    <td title="Persistence rank: how often this name has been in the top tier over the ranking window. Lower is better (1 = most persistent).">${r.rank ?? ""}</td>
                    <td title="Latest price (pence).">${r.price != null ? Number(r.price).toFixed(2) : ""}</td>
                    <td title="Today’s percentage price change. Shows immediate momentum or weakness on the current session.">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : ""}</td>
                    <td title="3-month price return. Positive values show medium-term upward momentum.">${r.ret_3m != null ? r.ret_3m.toFixed(1) + "%" : ""}</td>
                    <td title="Percentage distance from the 50-day moving average. Positive = trading above the 50-day MA (short-term trend support).">${r.pct_from_50ma != null ? r.pct_from_50ma.toFixed(1) : ""}</td>
                    <td title="Percentage distance from the 200-day moving average. Positive = trading above the 200-day MA (longer-term trend support).">${r.pct_from_200ma != null ? r.pct_from_200ma.toFixed(1) : ""}</td>
                    <td title="Trailing Price/Earnings ratio. Lower values (within the gate) suggest the name is not extremely expensive on recent earnings.">${f.pe_trailing != null ? Number(f.pe_trailing).toFixed(1) : ""}</td>
                    <td title="Price-to-Book ratio. Values under the gate indicate the market is not pricing the company at a large premium to its book value.">${f.price_to_book != null ? Number(f.price_to_book).toFixed(2) : ""}</td>
                    <td><input type="checkbox" class="cand-select" data-symbol="${r.symbol}"></td>
                </tr>`;
        }).join("");

        container.innerHTML = `
            <h2>Candidates</h2>
            <p style="color:#aaa; margin-top:0;">Rank ≤ ${rankMax} and fundamental gates (PE ${peMin}–${peMax}, P/B &lt; ${pbMax}${requireDiv ? ", dividend required" : ""}). Sorted best → worst.</p>
            <div style="margin:12px 0;">
                <button id="cand-add" class="mini-btn" style="background:#1e5c3a;">Add selected to Tracker</button>
            </div>
            <table id="candidates-table" class="data-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th>Sector</th>
                        <th title="Persistence rank: how often this name has been in the top tier over the ranking window. Lower is better (1 = most persistent).">Rank</th>
                        <th title="Latest price (pence).">Price</th>
                        <th title="Today’s percentage price change. Shows immediate momentum or weakness on the current session.">Day %</th>
                        <th title="3-month price return. Positive values show medium-term upward momentum.">3 m %</th>
                        <th title="Percentage distance from the 50-day moving average. Positive = trading above the 50-day MA (short-term trend support).">vs 50</th>
                        <th title="Percentage distance from the 200-day moving average. Positive = trading above the 200-day MA (longer-term trend support).">vs 200</th>
                        <th title="Trailing Price/Earnings ratio. Lower values (within the gate) suggest the name is not extremely expensive on recent earnings.">PE</th>
                        <th title="Price-to-Book ratio. Values under the gate indicate the market is not pricing the company at a large premium to its book value.">P/B</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>${body || `<tr><td colspan="12" style="text-align:center; color:#666;">No candidates match the current gates.</td></tr>`}</tbody>
            </table>
        `;

        document.getElementById("cand-add").onclick = () => {
            const selected = [...document.querySelectorAll(".cand-select:checked")].map(cb => cb.dataset.symbol);
            if (!selected.length) return;
            if (window.Tool3 && typeof window.Tool3.addSymbols === "function") {
                window.Tool3.addSymbols(selected);
            } else {
                alert("Selected: " + selected.join(", ") + "\n(Tracker add not wired yet)");
            }
        };

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("candidates-table"));
        }
    },

    async refreshPrices() {
        if (window.AppState.currentTool !== "7") return;
        try {
            const res = await fetch("/screener");
            const data = await res.json();
            const map = {};
            (data.rows || []).forEach(r => { map[r.symbol] = r; });

            document.querySelectorAll("#candidates-table tbody tr").forEach(tr => {
                const sym = tr.children[0].textContent.trim();
                const row = map[sym];
                if (!row) return;

                const priceCell = tr.children[4];
                const dayCell = tr.children[5];

                if (priceCell && row.price != null) {
                    const old = parseFloat(priceCell.textContent);
                    const neu = Number(row.price);
                    priceCell.textContent = neu.toFixed(2);
                    if (!isNaN(old) && old !== neu && window.triggerFlash) {
                        window.triggerFlash(priceCell, neu > old);
                    }
                }
                if (dayCell && row.change_pct != null) {
                    dayCell.textContent = row.change_pct.toFixed(2) + "%";
                }
            });
        } catch (e) { /* silent */ }
    }
};