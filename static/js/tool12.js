// static/js/tool12.js
// Tool 12 — Screeners
// Composite ranking (best first) with 1-year sparklines and click-to-enlarge modal.

window.Tool12 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading composite ranking…</div>`;

        try {
            const res = await fetch("/screens/composite");
            const data = await res.json();
            this.render(data.rows || []);
        } catch (e) {
            container.innerHTML = `<div style="padding:16px; color:#f87171;">Failed to load screen: ${e}</div>`;
        }
    },

    render(rows) {
        const container = document.getElementById("results");

        const tableRows = rows.map(r => `
            <tr>
                <td>${r.symbol}</td>
                <td>${(r.name || "").substring(0, 28)}</td>
                <td>${r.sector || ""}</td>
                <td>${r.composite_rank ?? ""}</td>
                <td>${r.composite_score != null ? r.composite_score.toFixed(1) : ""}</td>
                <td>${r.base_rank ?? ""}</td>
                <td>${r.ta_rank ?? ""}</td>
                <td>${r.fund_rank ?? ""}</td>
                <td>${r.price != null ? formatNumber(r.price) : ""}</td>
                <td class="${(r.change_pct || 0) >= 0 ? "positive" : "negative"}">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : ""}</td>
                <td><canvas class="spark composite-spark" width="120" height="32"
                            data-prices="${JSON.stringify(r.prices || [])}"
                            data-symbol="${r.symbol}"
                            data-name="${(r.name || "").replace(/"/g, "&quot;")}"
                            style="cursor:pointer;"></canvas></td>
            </tr>
        `).join("");

        container.innerHTML = `
            <div class="region-bar">
                <h3>Screeners — Composite (${rows.length})</h3>
                <div style="color:#7fdbff; font-size:0.85rem;">Ordered by weighted composite score</div>
            </div>
            <table class="data-table" id="screens-table">
                <thead>
                    <tr>
                        <th data-key="symbol">Symbol</th>
                        <th data-key="name">Name</th>
                        <th data-key="sector">Sector</th>
                        <th data-key="composite_rank">Comp Rank</th>
                        <th data-key="composite_score">Comp Score</th>
                        <th data-key="base_rank">Base</th>
                        <th data-key="ta_rank">TA</th>
                        <th data-key="fund_rank">Fund</th>
                        <th data-key="price">Price</th>
                        <th data-key="change_pct">Day %</th>
                        <th>Sparkline</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows || "<tr><td colspan='11'>No composite scores available. Run update_composite_score.py first.</td></tr>"}
                </tbody>
            </table>

            <!-- Large sparkline modal -->
            <div id="spark-modal" class="modal-overlay">
                <div class="modal-box" style="width:640px; max-width:95vw;">
                    <h3 id="spark-modal-title">Sparkline</h3>
                    <canvas id="spark-modal-canvas" width="600" height="220" style="width:100%; height:220px; background:#0d1b2a; border-radius:4px;"></canvas>
                    <div class="modal-actions">
                        <button class="mini-btn" id="spark-modal-close">Close</button>
                    </div>
                </div>
            </div>
        `;

        // Draw small sparklines and attach click handlers
        document.querySelectorAll("canvas.composite-spark").forEach(canvas => {
            try {
                const prices = JSON.parse(canvas.dataset.prices || "[]");
                this.drawSparkline(canvas, prices);

                canvas.addEventListener("click", () => {
                    this.openSparkModal(
                        canvas.dataset.symbol,
                        canvas.dataset.name,
                        prices
                    );
                });
            } catch (e) {
                console.warn("Sparkline draw failed", e);
            }
        });

        // Modal close
        const modal = document.getElementById("spark-modal");
        document.getElementById("spark-modal-close").addEventListener("click", () => {
            modal.classList.remove("active");
        });
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.remove("active");
        });

        if (window.makeTableSortable) {
            makeTableSortable(document.getElementById("screens-table"));
        }
    },

    openSparkModal(symbol, name, prices) {
        const modal = document.getElementById("spark-modal");
        const title = document.getElementById("spark-modal-title");
        const canvas = document.getElementById("spark-modal-canvas");

        title.textContent = `${symbol} — ${name || ""}`;
        this.drawSparkline(canvas, prices, true);
        modal.classList.add("active");
    },

    drawSparkline(canvas, values, large = false) {
        if (!canvas || !values || values.length < 2) return;
        const ctx = canvas.getContext("2d");
        const w = canvas.width = large ? 600 : (canvas.offsetWidth || 120);
        const h = canvas.height = large ? 220 : (canvas.offsetHeight || 32);
        ctx.clearRect(0, 0, w, h);

        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;
        const step = w / (values.length - 1);
        const pad = large ? 16 : 3;

        const points = values.map((v, i) => ({
            x: i * step,
            y: h - ((v - min) / range) * (h - pad * 2) - pad
        }));

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = "#7fdbff";
        ctx.lineWidth = large ? 2 : 1.2;
        ctx.stroke();
    }
};