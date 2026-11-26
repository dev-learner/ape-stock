// static/js/tool12.js
// Tool 12 — Screeners
// v1: Recovery Screen with 1-year sparklines, high→low→current overlay,
// and click-to-enlarge modal.

window.Tool12 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading Recovery Screen…</div>`;

        try {
            const res = await fetch("/screens/recovery");
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
                <td>${r.name || ""}</td>
                <td>${r.high_date || ""}</td>
                <td>${r.high_price != null ? r.high_price.toFixed(1) : ""}</td>
                <td>${r.low_date || ""}</td>
                <td>${r.low_price != null ? r.low_price.toFixed(1) : ""}</td>
                <td class="negative">${r.drawdown_pct != null ? r.drawdown_pct.toFixed(1) + "%" : ""}</td>
                <td class="positive">${r.bounce_pct != null ? r.bounce_pct.toFixed(1) + "%" : ""}</td>
                <td>${r.current != null ? r.current.toFixed(1) : ""}</td>
                <td>${r.rank != null ? r.rank : "—"}</td>
                <td><canvas class="spark recovery-spark" width="120" height="32"
                            data-prices="${JSON.stringify(r.prices || [])}"
                            data-high="${r.high_idx ?? ""}"
                            data-low="${r.low_idx ?? ""}"
                            data-current="${r.current_idx ?? ""}"
                            data-symbol="${r.symbol}"
                            data-name="${(r.name || "").replace(/"/g, "&quot;")}"
                            style="cursor:pointer;"></canvas></td>
            </tr>
        `).join("");

        container.innerHTML = `
            <div class="region-bar">
                <h3>Screeners — Recovery</h3>
                <div style="color:#7fdbff; font-size:0.85rem;">${rows.length} candidates</div>
            </div>
            <table class="data-table" id="screens-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th>High Date</th>
                        <th>High</th>
                        <th>Low Date</th>
                        <th>Low</th>
                        <th>Drawdown %</th>
                        <th>Bounce %</th>
                        <th>Current</th>
                        <th>Rank</th>
                        <th>Sparkline</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows || "<tr><td colspan='11'>No recovery candidates found.</td></tr>"}
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

        // Draw small sparklines
        document.querySelectorAll("canvas.recovery-spark").forEach(canvas => {
            try {
                const prices = JSON.parse(canvas.dataset.prices || "[]");
                const highIdx = canvas.dataset.high !== "" ? parseInt(canvas.dataset.high, 10) : null;
                const lowIdx = canvas.dataset.low !== "" ? parseInt(canvas.dataset.low, 10) : null;
                const currIdx = canvas.dataset.current !== "" ? parseInt(canvas.dataset.current, 10) : null;
                this.drawRecoverySparkline(canvas, prices, highIdx, lowIdx, currIdx);

                // Click to enlarge
                canvas.addEventListener("click", () => {
                    this.openSparkModal(
                        canvas.dataset.symbol,
                        canvas.dataset.name,
                        prices,
                        highIdx,
                        lowIdx,
                        currIdx
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

    openSparkModal(symbol, name, prices, highIdx, lowIdx, currIdx) {
        const modal = document.getElementById("spark-modal");
        const title = document.getElementById("spark-modal-title");
        const canvas = document.getElementById("spark-modal-canvas");

        title.textContent = `${symbol} — ${name || ""}`;
        this.drawRecoverySparkline(canvas, prices, highIdx, lowIdx, currIdx, true);
        modal.classList.add("active");
    },

    drawRecoverySparkline(canvas, values, highIdx, lowIdx, currIdx, large = false) {
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

        // Normal price line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = "#778da9";
        ctx.lineWidth = large ? 2 : 1.2;
        ctx.stroke();

        // Straight recovery path: high → low → current
        const pathPoints = [];
        if (highIdx != null && points[highIdx]) pathPoints.push(points[highIdx]);
        if (lowIdx != null && points[lowIdx]) pathPoints.push(points[lowIdx]);
        if (currIdx != null && points[currIdx]) pathPoints.push(points[currIdx]);

        if (pathPoints.length >= 2) {
            ctx.beginPath();
            ctx.moveTo(pathPoints[0].x, pathPoints[0].y);
            pathPoints.forEach(p => ctx.lineTo(p.x, p.y));
            ctx.strokeStyle = "#7fdbff";
            ctx.lineWidth = large ? 3 : 2;
            ctx.setLineDash(large ? [6, 4] : [3, 2]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Dots
            const radius = large ? 5 : 2.5;
            pathPoints.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = "#7fdbff";
                ctx.fill();
            });
        }
    }
};