// static/js/tool12.js
// Tool 12 — Screeners
// Composite ranking with live weight inputs, Expand (TA + Fund detail rows),
// component scores, sparklines (MAs + largest-drawdown path), modal,
// select-all and Track! button.

window.Tool12 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `<div style="padding:16px; color:#aaa;">Loading composite ranking…</div>`;

        try {
            const [compRes, settingsRes] = await Promise.all([
                fetch("/screens/composite"),
                fetch("/settings/get")
            ]);
            const data = await compRes.json();
            const settings = settingsRes.ok ? await settingsRes.json() : {};
            this.render(data.rows || [], settings, data.limited);
        } catch (e) {
            container.innerHTML = `<div style="padding:16px; color:#f87171;">Failed to load screen: ${e}</div>`;
        }
    },

    render(rows, settings = {}, dataLimited = false) {
        const container = document.getElementById("results");

        const fmt = (v) => v != null ? Number(v).toFixed(1) : "";

        const wBase = settings.weight_base ?? "30";
        const wTa = settings.weight_ta ?? "25";
        const wFund = settings.weight_fund ?? "25";
        const wPers = settings.weight_persistence ?? "10";
        const wRec = settings.weight_recovery ?? "10";

        const limitNote = dataLimited ? ` (top ${rows.length})` : ` (${rows.length})`;

        const tableRows = rows.map(r => `
            <tr>
                <td>${r.symbol}</td>
                <td>${(r.name || "").substring(0, 28)}</td>
                <td>${r.sector || ""}</td>
                <td class="num">${r.composite_rank ?? ""}</td>
                <td class="num">${fmt(r.composite_score)}</td>
                <td class="num">${fmt(r.base_score)}</td>
                <td class="num">${fmt(r.ta_score)}</td>
                <td class="num">${fmt(r.fund_score)}</td>
                <td class="num">${fmt(r.persistence_score)}</td>
                <td class="num">${fmt(r.recovery_score)}</td>
                <td class="num">${r.price != null ? formatNumber(r.price) : ""}</td>
                <td class="num ${(r.change_pct || 0) >= 0 ? "positive" : "negative"}">${r.change_pct != null ? r.change_pct.toFixed(2) + "%" : ""}</td>
                <td><canvas class="spark composite-spark" width="120" height="32"
                            data-prices="${JSON.stringify(r.prices || [])}"
                            data-symbol="${r.symbol}"
                            data-name="${(r.name || "").replace(/"/g, "&quot;")}"
                            style="cursor:pointer;"></canvas></td>
                <td style="text-align:center;"><input type="checkbox" data-symbol="${r.symbol}"></td>
            </tr>
        `).join("");

        container.innerHTML = `
            <div class="region-bar" style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <h3 style="margin:0;">Composite${limitNote} using weights:</h3>
                <div style="display:flex; gap:12px; align-items:center; font-size:0.9rem;">
                    <label>Base <input type="number" id="w-base" value="${wBase}" min="0" max="100" step="1" style="width:60px;"></label>
                    <label>TA <input type="number" id="w-ta" value="${wTa}" min="0" max="100" step="1" style="width:60px;"></label>
                    <label>Fund <input type="number" id="w-fund" value="${wFund}" min="0" max="100" step="1" style="width:60px;"></label>
                    <label>Pers <input type="number" id="w-pers" value="${wPers}" min="0" max="100" step="1" style="width:60px;"></label>
                    <label>Rec <input type="number" id="w-rec" value="${wRec}" min="0" max="100" step="1" style="width:60px;"></label>
                </div>
                <div style="display:flex; gap:8px;">
                    <button id="expand-btn" class="mini-btn">Expand</button>
                    <button id="add-to-tracker" class="mini-btn" style="background:#1e5c3a;">Track!</button>
                </div>
            </div>
            <table class="data-table" id="screens-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Name</th>
                        <th>Sector</th>
                        <th class="num">Rank</th>
                        <th class="num">Score</th>
                        <th class="num">Base</th>
                        <th class="num">TA</th>
                        <th class="num">Fund</th>
                        <th class="num">Pers</th>
                        <th class="num">Rec</th>
                        <th class="num">Price</th>
                        <th class="num">Day %</th>
                        <th>Sparkline</th>
                        <th style="text-align:center;"><input type="checkbox" id="select-all" title="Select / deselect all"></th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows || "<tr><td colspan='14'>No composite scores available.</td></tr>"}
                </tbody>
            </table>

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

        // Sparklines
        document.querySelectorAll("canvas.composite-spark").forEach(canvas => {
            try {
                const prices = JSON.parse(canvas.dataset.prices || "[]");
                this.drawSparkline(canvas, prices);
                canvas.addEventListener("click", () => {
                    this.openSparkModal(canvas.dataset.symbol, canvas.dataset.name, prices);
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

        // Select / deselect all
        const selectAll = document.getElementById("select-all");
        if (selectAll) {
            selectAll.addEventListener("change", () => {
                document.querySelectorAll("#screens-table tbody input[type=checkbox]").forEach(cb => {
                    cb.checked = selectAll.checked;
                });
            });
        }

        // Expand button
        let expanded = false;
        document.getElementById("expand-btn")?.addEventListener("click", () => {
            expanded = !expanded;
            document.getElementById("expand-btn").classList.toggle("active", expanded);
            this.toggleExpand(rows, expanded);
        });

        // Track! button
        document.getElementById("add-to-tracker")?.addEventListener("click", async () => {
            const checked = [...document.querySelectorAll("#screens-table tbody input[type=checkbox]:checked")];
            if (!checked.length) {
                alert("No symbols selected");
                return;
            }
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

        // Live weight updates
        const weightInputs = ["w-base", "w-ta", "w-fund", "w-pers", "w-rec"];
        const keyMap = {
            "w-base": "weight_base",
            "w-ta": "weight_ta",
            "w-fund": "weight_fund",
            "w-pers": "weight_persistence",
            "w-rec": "weight_recovery"
        };

        weightInputs.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.addEventListener("change", async () => {
                const payload = {};
                weightInputs.forEach(i => {
                    const input = document.getElementById(i);
                    if (input) payload[keyMap[i]] = input.value;
                });
                try {
                    await fetch("/settings/save", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload)
                    });
                    this.show();
                } catch (e) {
                    console.warn("Weight update failed", e);
                }
            });
        });
    },

    toggleExpand(rows, expanded) {
        document.querySelectorAll(".detail-row").forEach(el => el.remove());
        if (!expanded) return;

        const checked = [...document.querySelectorAll("#screens-table tbody input[type=checkbox]:checked")];
        checked.forEach(cb => {
            const sym = cb.dataset.symbol;
            const row = rows.find(r => r.symbol === sym);
            if (!row) return;
            const tr = cb.closest("tr");

            const fmt = (v, dec = 1, suffix = "") =>
                v != null ? Number(v).toFixed(dec) + suffix : "—";

            const taRow = document.createElement("tr");
            taRow.className = "detail-row";
            taRow.innerHTML = `
                <td colspan="14" style="background:#13293d; padding:10px 16px;">
                    <div style="display:flex; flex-wrap:wrap; gap:18px 28px; font-size:0.88rem; line-height:1.6;">
                        <span><strong style="color:#7fdbff;">TA</strong></span>
                        <span>3m <strong>${fmt(row.ret_3m, 1, "%")}</strong></span>
                        <span>6m <strong>${fmt(row.ret_6m, 1, "%")}</strong></span>
                        <span>vs 50MA <strong>${fmt(row.pct_from_50ma, 1, "%")}</strong></span>
                        <span>vs 200MA <strong>${fmt(row.pct_from_200ma, 1, "%")}</strong></span>
                        <span>Dist 52w <strong>${fmt(row.dist_52w_high, 1, "%")}</strong></span>
                        <span>Vol 20d <strong>${fmt(row.vol_20d, 1)}</strong></span>
                    </div>
                </td>`;

            const fundRow = document.createElement("tr");
            fundRow.className = "detail-row";
            fundRow.innerHTML = `
                <td colspan="14" style="background:#0d1b2a; padding:10px 16px; border-bottom:2px solid #1b3a4b;">
                    <div style="display:flex; flex-wrap:wrap; gap:18px 28px; font-size:0.88rem; line-height:1.6;">
                        <span><strong style="color:#7fdbff;">Fund</strong></span>
                        <span>PE <strong>${fmt(row.pe_trailing, 1)}</strong></span>
                        <span>Fwd PE <strong>${fmt(row.pe_forward, 1)}</strong></span>
                        <span>P/B <strong>${fmt(row.price_to_book, 2)}</strong></span>
                        <span>Yield <strong>${fmt(row.dividend_yield, 2, "%")}</strong></span>
                        <span>ROE <strong>${fmt(row.roe, 1, "%")}</strong></span>
                        <span>Margin <strong>${fmt(row.profit_margin, 1, "%")}</strong></span>
                        <span>Rev Growth <strong>${fmt(row.revenue_growth, 1, "%")}</strong></span>
                    </div>
                </td>`;

            tr.after(fundRow);
            tr.after(taRow);
        });
    },

    openSparkModal(symbol, name, prices) {
        const modal = document.getElementById("spark-modal");
        document.getElementById("spark-modal-title").textContent = `${symbol} — ${name || ""}`;
        this.drawSparkline(document.getElementById("spark-modal-canvas"), prices, true);
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

        const toPoint = (v, i) => ({
            x: i * step,
            y: h - ((v - min) / range) * (h - pad * 2) - pad
        });

        const points = values.map((v, i) => toPoint(v, i));

        const ma = (period) => {
            const result = [];
            for (let i = 0; i < values.length; i++) {
                if (i < period - 1) result.push(null);
                else {
                    const slice = values.slice(i - period + 1, i + 1);
                    result.push(slice.reduce((a, b) => a + b, 0) / period);
                }
            }
            return result;
        };

        const drawMA = (maValues, color, width) => {
            ctx.beginPath();
            let started = false;
            maValues.forEach((v, i) => {
                if (v == null) return;
                const p = toPoint(v, i);
                if (!started) { ctx.moveTo(p.x, p.y); started = true; }
                else ctx.lineTo(p.x, p.y);
            });
            ctx.strokeStyle = color;
            ctx.lineWidth = width;
            ctx.stroke();
        };

        if (values.length >= 50) drawMA(ma(50), large ? "#fbbf24" : "#fbbf2488", large ? 1.5 : 1);
        if (values.length >= 200) drawMA(ma(200), large ? "#f87171" : "#f8717188", large ? 1.5 : 1);

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = "#7fdbff";
        ctx.lineWidth = large ? 2 : 1.2;
        ctx.stroke();

        let bestHighIdx = 0, bestLowIdx = 0, maxDrawdown = 0;
        for (let i = 0; i < values.length; i++) {
            for (let j = i + 1; j < values.length; j++) {
                const dd = (values[j] / values[i] - 1);
                if (dd < maxDrawdown) {
                    maxDrawdown = dd;
                    bestHighIdx = i;
                    bestLowIdx = j;
                }
            }
        }

        if (maxDrawdown < -0.05) {
            const pathPoints = [points[bestHighIdx], points[bestLowIdx], points[values.length - 1]];
            ctx.beginPath();
            ctx.moveTo(pathPoints[0].x, pathPoints[0].y);
            pathPoints.forEach(p => ctx.lineTo(p.x, p.y));
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = large ? 2.5 : 1.5;
            ctx.setLineDash(large ? [6, 4] : [3, 2]);
            ctx.stroke();
            ctx.setLineDash([]);

            const radius = large ? 5 : 2.5;
            pathPoints.forEach(p => {
                ctx.beginPath();
                ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = "#ffffff";
                ctx.fill();
            });
        }
    }
};