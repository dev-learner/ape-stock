// static/js/tool6.js
window.Tool6 = {
    async show() {
        const res = await fetch("/fundamentals");
        const data = await res.json();
        this.render(data.rows || []);
    },

    render(rows) {
        const container = document.getElementById("results");
        container.innerHTML = `
            <h2>Fundamentals (${rows.length})</h2>
            <table class="data-table" id="fund-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
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
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                        <tr>
                            <td>${r.symbol}</td>
                            <td>${(r.name || "").substring(0, 28)}</td>
                            <td>${r.sector || ""}</td>
                            <td>${r.market_cap ? (r.market_cap / 1e9).toFixed(2) + "bn" : ""}</td>
                            <td>${r.pe_trailing != null ? r.pe_trailing.toFixed(1) : ""}</td>
                            <td>${r.pe_forward != null ? r.pe_forward.toFixed(1) : ""}</td>
                            <td>${r.price_to_book != null ? r.price_to_book.toFixed(2) : ""}</td>
                            <td>${r.dividend_yield != null ? (r.dividend_yield * 100).toFixed(2) + "%" : ""}</td>
                            <td>${r.roe != null ? (r.roe * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.profit_margin != null ? (r.profit_margin * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.revenue_growth != null ? (r.revenue_growth * 100).toFixed(1) + "%" : ""}</td>
                            <td>${r.beta != null ? r.beta.toFixed(2) : ""}</td>
                            <td>${r.current_ratio != null ? r.current_ratio.toFixed(2) : ""}</td>
                        </tr>`).join("")}
                </tbody>
            </table>
        `;

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("fund-table"));
        }
    }
};