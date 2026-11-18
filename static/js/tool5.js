// static/js/tool5.js
window.Tool5 = {
    async show() {
        await this.render();
    },

    async render() {
        const container = document.getElementById("results");
        const sumRes = await fetch("/portfolio/summary");
        const sum = await sumRes.json();

        container.innerHTML = `
            <div class="portfolio-header">
                <h1>Portfolio</h1>
                <h2>Cash Balance £${sum.cash.toLocaleString(undefined,{minimumFractionDigits:2})} 
                    — Value £${sum.value.toLocaleString(undefined,{minimumFractionDigits:2})} 
                    — P/L ${sum.pl_pct.toFixed(2)}%</h2>
                <hr style="border:0; border-top:1px solid #334155; margin:12px 0 20px;">
            </div>

            <h3>Holdings</h3>
            <div class="portfolio-buttons">
                <button id="btn-cash" class="mini-btn btn-cash">Cash</button>
                <button id="btn-buy" class="mini-btn btn-buy">Buy</button>
                <button id="btn-sell" class="mini-btn btn-sell">Sell</button>
                <button id="btn-reset" class="mini-btn btn-reset" title="Clear all portfolio data">Reset</button>
            </div>

            <table class="data-table" id="holdings-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="quantity">Qty</th>
                        <th data-key="avg_cost">Avg. Price (£)</th>
                        <th data-key="total_cost">Total (£)</th>
                        <th data-key="last_price_pence">Price (p)</th>
                        <th data-key="value">Value (£)</th>
                        <th data-key="pnl">P/L £</th>
                        <th data-key="pnl_pct">P/L %</th>
                    </tr>
                </thead>
                <tbody>
                    ${sum.positions.map(p => `
                        <tr>
                            <td>${p.symbol}</td>
                            <td>${(p.name || "").substring(0, 28)}</td>
                            <td>${p.quantity}</td>
                            <td>${Number(p.avg_cost).toFixed(4)}</td>
                            <td>${Number(p.total_cost).toFixed(2)}</td>
                            <td class="live-price" data-symbol="${p.symbol}">${Number(p.last_price_pence).toFixed(2)}</td>
                            <td>${Number(p.value).toFixed(2)}</td>
                            <td class="${p.pnl >= 0 ? "positive" : "negative"}">${Number(p.pnl).toFixed(2)}</td>
                            <td class="${p.pnl_pct >= 0 ? "positive" : "negative"}">${Number(p.pnl_pct).toFixed(1)}%</td>
                        </tr>`).join("")}
                </tbody>
            </table>

            <h3 style="margin-top:28px;">Transactions</h3>
            <div class="tx-toolbar">
                <div class="left">
                    <button class="mini-btn filter-btn" data-filter="all">All</button>
                    <button class="mini-btn filter-btn" data-filter="cash">Cash</button>
                    <button class="mini-btn filter-btn" data-filter="shares">Shares</button>
                </div>
                <div class="right">
                    <button id="btn-export" class="mini-btn filter-btn">Export</button>
                    <button id="btn-import" class="mini-btn filter-btn">Import</button>
                </div>
            </div>
            <div id="tx-container"></div>

            <!-- Cash Modal -->
            <div id="modal-cash" class="modal-overlay">
                <div class="modal-box">
                    <h3>Cash Transaction</h3>
                    <label>Date</label>
                    <input type="date" id="cash-date">
                    <label>Amount (£)</label>
                    <input type="number" id="cash-amount" step="0.01" min="0.01">
                    <div class="modal-actions">
                        <button id="cash-deposit" class="mini-btn btn-buy">Deposit</button>
                        <button id="cash-withdraw" class="mini-btn btn-sell">Withdraw</button>
                        <button id="cash-cancel" class="mini-btn">Cancel</button>
                    </div>
                </div>
            </div>

            <!-- Buy Modal -->
            <div id="modal-buy" class="modal-overlay">
                <div class="modal-box">
                    <h3>Buy Stock</h3>
                    <label>Date</label>
                    <input type="date" id="buy-date">
                    <label>Symbol</label>
                    <div style="position:relative;">
                        <input type="text" id="buy-symbol" autocomplete="off">
                        <div id="buy-search-results" class="search-results"></div>
                    </div>
                    <label>Quantity</label>
                    <input type="number" id="buy-qty" step="any" min="0">
                    <label>Price</label>
                    <input type="number" id="buy-price" step="0.0001" min="0">
                    <label>Stamp Duty (£)</label>
                    <input type="text" id="buy-stamp-amount" readonly>
                    <label>Total (£)</label>
                    <input type="text" id="buy-total" readonly>
                    <div class="modal-actions">
                        <button id="buy-save" class="mini-btn btn-buy">Save</button>
                        <button id="buy-cancel" class="mini-btn">Cancel</button>
                    </div>
                </div>
            </div>

            <!-- Sell Modal -->
            <div id="modal-sell" class="modal-overlay">
                <div class="modal-box">
                    <h3>Sell Stock</h3>
                    <label>Date</label>
                    <input type="date" id="sell-date">
                    <label>Symbol</label>
                    <select id="sell-symbol"></select>
                    <label>Quantity</label>
                    <input type="number" id="sell-qty" step="any" min="0">
                    <label>Price</label>
                    <input type="number" id="sell-price" step="0.0001" min="0">
                    <label>Total (£)</label>
                    <input type="text" id="sell-total" readonly>
                    <div class="modal-actions">
                        <button id="sell-save" class="mini-btn btn-sell">Save</button>
                        <button id="sell-cancel" class="mini-btn">Cancel</button>
                    </div>
                </div>
            </div>

            <!-- Export Modal -->
            <div id="modal-export" class="modal-overlay">
                <div class="modal-box">
                    <h3>Export Transactions</h3>
                    <label>Format</label>
                    <select id="export-format">
                        <option value="json">JSON</option>
                        <option value="csv">CSV</option>
                    </select>
                    <div class="modal-actions">
                        <button id="export-go" class="mini-btn filter-btn">Export</button>
                        <button id="export-cancel" class="mini-btn">Cancel</button>
                    </div>
                </div>
            </div>

            <!-- Import Modal -->
            <div id="modal-import" class="modal-overlay">
                <div class="modal-box">
                    <h3>Import Transactions</h3>
                    <p style="font-size:0.9rem; color:#94a3b8;">This will erase the current portfolio and replace it with the file contents.</p>
                    <label>File (.json or .csv)</label>
                    <input type="file" id="import-file" accept=".json,.csv">
                    <div class="modal-actions">
                        <button id="import-go" class="mini-btn filter-btn">Import</button>
                        <button id="import-cancel" class="mini-btn">Cancel</button>
                    </div>
                </div>
            </div>
        `;

        this.loadTransactions("all");
        this.bindEvents();

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("holdings-table"));
        }
    },

    async loadTransactions(filter) {
        const res = await fetch(`/portfolio/transactions?filter=${filter}`);
        const rows = await res.json();
        const html = `
            <table class="data-table" id="tx-table">
                <thead>
                    <tr>
                        <th data-key="id">#</th>
                        <th data-key="ts">Date</th>
                        <th data-key="type">Type</th>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="quantity">Qty</th>
                        <th data-key="price">Price</th>
                        <th data-key="costs">Costs</th>
                        <th data-key="cash_impact">Cash Impact</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                        <tr>
                            <td>${r.id}</td>
                            <td>${r.ts.substring(0,10)}</td>
                            <td>${r.type}</td>
                            <td>${r.symbol || ""}</td>
                            <td title="${r.name || ''}">${(r.name || "").substring(0, 32)}</td>
                            <td>${r.quantity || ""}</td>
                            <td>${r.price ? Number(r.price).toFixed(4) : ""}</td>
                            <td>${r.costs ? Number(r.costs).toFixed(2) : ""}</td>
                            <td>${Number(r.cash_impact).toFixed(2)}</td>
                            <td>${r.notes || ""}</td>
                        </tr>`).join("")}
                </tbody>
            </table>`;
        document.getElementById("tx-container").innerHTML = html;

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("tx-table"));
        }
    },

    bindEvents() {
        const show = id => document.getElementById(id).classList.add("active");
        const hide = id => document.getElementById(id).classList.remove("active");

        document.getElementById("btn-cash").onclick = () => {
            document.getElementById("cash-date").value = new Date().toISOString().slice(0,10);
            show("modal-cash");
        };
        document.getElementById("btn-buy").onclick = () => {
            document.getElementById("buy-date").value = new Date().toISOString().slice(0,10);
            show("modal-buy");
        };
        document.getElementById("btn-sell").onclick = async () => {
            const sum = await (await fetch("/portfolio/summary")).json();
            const sel = document.getElementById("sell-symbol");
            sel.innerHTML = sum.positions.map(p => `<option value="${p.symbol}">${p.symbol} (${p.quantity})</option>`).join("");
            document.getElementById("sell-date").value = new Date().toISOString().slice(0,10);
            show("modal-sell");
        };
        document.getElementById("btn-reset").onclick = async () => {
            if (!confirm("Clear ALL portfolio data? This cannot be undone.")) return;
            await fetch("/portfolio/reset", { method: "POST" });
            this.render();
        };

        document.querySelectorAll(".filter-btn").forEach(b => {
            if (b.dataset.filter) {
                b.onclick = () => this.loadTransactions(b.dataset.filter);
            }
        });

        document.getElementById("btn-export").onclick = () => show("modal-export");
        document.getElementById("export-cancel").onclick = () => hide("modal-export");
        document.getElementById("export-go").onclick = () => {
            const fmt = document.getElementById("export-format").value;
            window.location = `/portfolio/export?format=${fmt}`;
            hide("modal-export");
        };

        document.getElementById("btn-import").onclick = () => show("modal-import");
        document.getElementById("import-cancel").onclick = () => hide("modal-import");
        document.getElementById("import-go").onclick = async () => {
            const fileInput = document.getElementById("import-file");
            if (!fileInput.files.length) { alert("Select a file"); return; }
            if (!confirm("This will erase the current portfolio. Continue?")) return;

            const form = new FormData();
            form.append("file", fileInput.files[0]);
            const res = await fetch("/portfolio/import", { method: "POST", body: form });
            if (res.ok) {
                hide("modal-import");
                this.render();
            } else {
                const err = await res.json();
                alert(err.error || "Import failed");
            }
        };

        document.getElementById("cash-cancel").onclick = () => hide("modal-cash");
        document.getElementById("cash-deposit").onclick = () => this.doCash("deposit");
        document.getElementById("cash-withdraw").onclick = () => this.doCash("withdraw");

        document.getElementById("buy-cancel").onclick = () => hide("modal-buy");
        const updateBuy = () => {
            const qty = parseFloat(document.getElementById("buy-qty").value) || 0;
            const price = parseFloat(document.getElementById("buy-price").value) || 0;
            const stampPct = parseFloat(localStorage.getItem("stampPct") || "0.5");
            const stamp = qty * price * (stampPct / 100);
            document.getElementById("buy-stamp-amount").value = stamp.toFixed(2);
            document.getElementById("buy-total").value = (qty * price + stamp).toFixed(2);
        };
        ["buy-qty", "buy-price"].forEach(id => document.getElementById(id).addEventListener("input", updateBuy));

        const symInput = document.getElementById("buy-symbol");
        const resultsDiv = document.getElementById("buy-search-results");
        let searchTimer;
        symInput.addEventListener("input", () => {
            clearTimeout(searchTimer);
            const q = symInput.value.trim();
            if (q.length < 1) { resultsDiv.style.display = "none"; return; }
            searchTimer = setTimeout(async () => {
                const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
                const items = await res.json();
                resultsDiv.innerHTML = items.slice(0, 8).map(i =>
                    `<div data-symbol="${i.symbol}">${i.symbol} — ${(i.name || "").substring(0, 30)}</div>`
                ).join("");
                resultsDiv.style.display = items.length ? "block" : "none";
            }, 200);
        });
        resultsDiv.addEventListener("click", e => {
            if (e.target.dataset.symbol) {
                symInput.value = e.target.dataset.symbol;
                resultsDiv.style.display = "none";
            }
        });
        document.addEventListener("click", e => {
            if (!symInput.contains(e.target) && !resultsDiv.contains(e.target)) {
                resultsDiv.style.display = "none";
            }
        });

        document.getElementById("buy-save").onclick = () => this.doBuy();

        document.getElementById("sell-cancel").onclick = () => hide("modal-sell");
        const updateSell = () => {
            const qty = parseFloat(document.getElementById("sell-qty").value) || 0;
            const price = parseFloat(document.getElementById("sell-price").value) || 0;
            document.getElementById("sell-total").value = (qty * price).toFixed(2);
        };
        ["sell-qty", "sell-price"].forEach(id => document.getElementById(id).addEventListener("input", updateSell));
        document.getElementById("sell-save").onclick = () => this.doSell();
    },

    async doCash(action) {
        const amount = parseFloat(document.getElementById("cash-amount").value);
        const date = document.getElementById("cash-date").value;
        const res = await fetch("/portfolio/cash", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ amount, action, date })
        });
        if (res.ok) {
            document.getElementById("modal-cash").classList.remove("active");
            this.render();
        } else {
            const err = await res.json();
            alert(err.error || "Failed");
        }
    },

    async doBuy() {
        const payload = {
            date: document.getElementById("buy-date").value,
            symbol: document.getElementById("buy-symbol").value.trim(),
            quantity: parseFloat(document.getElementById("buy-qty").value),
            price: parseFloat(document.getElementById("buy-price").value)
        };
        const res = await fetch("/portfolio/buy", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            document.getElementById("modal-buy").classList.remove("active");
            this.render();
        } else {
            const err = await res.json();
            alert(err.error || "Failed");
        }
    },

    async doSell() {
        const payload = {
            date: document.getElementById("sell-date").value,
            symbol: document.getElementById("sell-symbol").value,
            quantity: parseFloat(document.getElementById("sell-qty").value),
            price: parseFloat(document.getElementById("sell-price").value)
        };
        const res = await fetch("/portfolio/sell", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            document.getElementById("modal-sell").classList.remove("active");
            this.render();
        } else {
            const err = await res.json();
            alert(err.error || "Failed");
        }
    },

    async refreshPrices() {
        try {
            const res = await fetch("/portfolio/summary");
            const sum = await res.json();
            sum.positions.forEach(p => {
                const cell = document.querySelector(`.live-price[data-symbol="${p.symbol}"]`);
                if (cell) cell.textContent = Number(p.last_price_pence).toFixed(2);
            });
        } catch (e) {}
    }
};