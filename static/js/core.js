// static/js/core.js
window.AppState = {
    selectedRisers: new Set(),
    selectedFallers: new Set(),
    filterSelectedRisers: false,
    filterSelectedFallers: false,
    sortState: { risers: { key: null, dir: 1 }, fallers: { key: null, dir: 1 } },
    currentTool: null,
    wlSort: { key: null, dir: 1 },
    wlPrevOrder: null,
    rawRisers: [],
    rawFallers: [],
    currentRisersIndex: "ALL",
    currentFallersIndex: "ALL",
    pollOrder: JSON.parse(localStorage.getItem("pollOrder") || "null"),
    pollActive: localStorage.getItem("pollActive") === "true",
    pollSort: JSON.parse(localStorage.getItem("pollSort") || "null"),
    pollPrices: JSON.parse(localStorage.getItem("pollPrices") || "null"),
    pollActive: localStorage.getItem("pollActive") === "true",
    pollSort: JSON.parse(localStorage.getItem("pollSort") || "null"),
    expandSelectedRisers: false,
    expandSelectedFallers: false,
};


function formatNumber(value, type = "price") {
    if (value == null || isNaN(value)) return "";
    const abs = Math.abs(value);
    if (type === "volume") return value.toLocaleString();
    let decimals = 2;
    if (abs === 0) decimals = 2;
    else if (abs < 0.0001) decimals = 6;
    else if (abs < 0.01) decimals = 4;
    else if (abs < 1) decimals = 3;
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function tradingViewSymbol(symbol, indexKey) {
    if (!symbol) return "";
    if (indexKey === "100" || indexKey === "250" || (indexKey && (indexKey.includes("100") || indexKey.includes("250")))) {
        const clean = symbol.replace(/\.(L|IL)$/i, "");
        return `LSE:${clean}`;
    }
    return symbol;
}

function buildSymbolLink(symbol, indexKey) {
    const tvSym = tradingViewSymbol(symbol, indexKey);
    return `<a href="https://www.tradingview.com/chart/w4mAadQ7/?symbol=${encodeURIComponent(tvSym)}" target="_blank" rel="noopener">${symbol}</a>`;
}

function attachCheckboxListeners(containerId, selectedSet) {
    document.querySelectorAll(`#${containerId} input[type=checkbox]`).forEach(cb => {
        cb.addEventListener("change", () => {
            if (cb.checked) selectedSet.add(cb.dataset.symbol);
            else selectedSet.delete(cb.dataset.symbol);
        });
    });
}

function makeTableSortable(table, options = {}) {
    if (!table) return;
    const getVal = options.getValue || ((cell) => cell.textContent.trim());
    let sortKey = null;
    let sortDir = 1;

    table.querySelectorAll("th[data-key]").forEach(th => {
        th.style.cursor = "pointer";
        th.addEventListener("click", () => {
            const key = th.dataset.key;
            if (sortKey === key) sortDir *= -1;
            else { sortKey = key; sortDir = 1; }

            const tbody = table.querySelector("tbody");
            const rows = [...tbody.querySelectorAll("tr")];
            const colIndex = th.cellIndex;

            rows.sort((a, b) => {
                if (a.classList.contains("details-row") || b.classList.contains("details-row")) return 0;

                const cellA = a.children[colIndex];
                const cellB = b.children[colIndex];
                if (!cellA || !cellB) return 0;

                let va = getVal(cellA);
                let vb = getVal(cellB);
                const na = parseFloat(String(va).replace(/[^0-9.-]/g, ""));
                const nb = parseFloat(String(vb).replace(/[^0-9.-]/g, ""));

                const aEmpty = isNaN(na) || va === "";
                const bEmpty = isNaN(nb) || vb === "";

                // Empty values always sort last, regardless of direction
                if (aEmpty && bEmpty) return 0;
                if (aEmpty) return 1;
                if (bEmpty) return -1;

                if (!isNaN(na) && !isNaN(nb)) return (na - nb) * sortDir;
                return String(va).localeCompare(String(vb)) * sortDir;
            });

            // Keep details rows attached to their main row
            const details = [...tbody.querySelectorAll("tr.details-row")];
            rows.forEach(r => {
                if (r.classList.contains("details-row")) return; // already handled
                tbody.appendChild(r);
                const sym = r.dataset.symbol;
                const det = details.find(d => d.previousElementSibling === r || d.dataset.symbol === sym);
                if (det) tbody.appendChild(det);
            });

            // Update sort arrows WITHOUT destroying child elements
            table.querySelectorAll("th[data-key]").forEach(h => {
                // Remove only the arrow text node, leave any inputs alone
                [...h.childNodes].forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        node.textContent = node.textContent.replace(/ ↑| ↓/, "");
                    }
                });
            });
            // Append arrow as a text node
            th.appendChild(document.createTextNode(sortDir === 1 ? " ↑" : " ↓"));

            if (options.onSort) options.onSort(key, sortDir);
        });
    });
}

function drawSparkline(canvas, values, style = "line") {
    if (!canvas || !values || values.length < 2) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width = canvas.offsetWidth || 80;
    const h = canvas.height = canvas.offsetHeight || 24;
    ctx.clearRect(0, 0, w, h);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const step = w / (values.length - 1);

    const points = values.map((v, i) => ({
        x: i * step,
        y: h - ((v - min) / range) * (h - 4) - 2
    }));

    ctx.lineWidth = 1.5;
    if (style === "bars") {
        points.forEach((p, i) => {
            const up = i === 0 || values[i] >= values[i - 1];
            ctx.fillStyle = up ? "#4ade80" : "#f87171";
            const barH = Math.abs(p.y - h / 2);
            ctx.fillRect(p.x - 1, Math.min(p.y, h / 2), 2, barH || 1);
        });
        return;
    }
    if (style === "winloss") {
        points.forEach((p, i) => {
            if (i === 0) return;
            ctx.fillStyle = values[i] >= values[i - 1] ? "#4ade80" : "#f87171";
            ctx.fillRect(p.x - 1, h / 2 - 3, 2, 6);
        });
        return;
    }

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(p => ctx.lineTo(p.x, p.y));
    if (style === "gradient") {
        const grad = ctx.createLinearGradient(0, 0, w, 0);
        grad.addColorStop(0, "#4ade80");
        grad.addColorStop(1, "#f87171");
        ctx.strokeStyle = grad;
    } else {
        ctx.strokeStyle = values[values.length - 1] >= values[0] ? "#4ade80" : "#f87171";
    }
    ctx.stroke();

    if (style === "area") {
        ctx.lineTo(points[points.length - 1].x, h);
        ctx.lineTo(points[0].x, h);
        ctx.closePath();
        ctx.fillStyle = "rgba(74, 222, 128, 0.15)";
        ctx.fill();
    }
}

function triggerFlash(cell, isPositive) {
    if (!cell) return;
    const color = isPositive ? "#4ade80" : "#f87171";
    cell.style.transition = "none";
    cell.style.backgroundColor = color;
    cell.style.color = "#0d1b2a";
    setTimeout(() => {
        cell.style.transition = "background-color 2.2s ease-out, color 2.2s ease-out";
        cell.style.backgroundColor = "";
        cell.style.color = "";
    }, 50);
    setTimeout(() => {
        cell.style.transition = "";
    }, 2300);
}

let refreshTimer = null;
let countdownInterval = null;
let secondsLeft = 0;
let lastFtseCurrent = null;
let ftseCountdownTimer = null;

function stopAutoRefresh() {
    clearInterval(refreshTimer);
    clearInterval(countdownInterval);
    refreshTimer = null;
    countdownInterval = null;
    const cd = document.getElementById("countdown");
    if (cd) cd.textContent = "";
}

function startAutoRefresh() {
    stopAutoRefresh();
    const duration = parseInt(localStorage.getItem("updateDuration") || "0", 10);
    if (duration <= 0) return;
    secondsLeft = duration;
    document.getElementById("countdown").textContent = `Next refresh: ${secondsLeft}s`;
    countdownInterval = setInterval(() => {
        secondsLeft--;
        if (secondsLeft <= 0) secondsLeft = duration;
        document.getElementById("countdown").textContent = `Next refresh: ${secondsLeft}s`;
    }, 1000);
    refreshTimer = setInterval(() => {
        if (typeof window.refreshVisible === "function") window.refreshVisible();
    }, duration * 1000);
    if (window.AppState.currentTool === "4" && window.Tool4 && Tool4.refreshPrices) {
        Tool4.refreshPrices();
    }
}

function nextOpenDescription(nowIso) {
    if (!nowIso) return null;
    const ukNow = new Date(nowIso);
    const day = ukNow.getDay();
    const openToday = new Date(ukNow);
    openToday.setHours(8, 0, 0, 0);
    const closeToday = new Date(ukNow);
    closeToday.setHours(16, 30, 0, 0);

    let target = new Date(openToday);
    let label = "";

    if (day === 0) {                       // Sunday
        label = "Opens [tomorrow in]:";
        target.setDate(target.getDate() + 1);
    } else if (day === 6) {                // Saturday
        label = "Opens [on Monday in]:";
        target.setDate(target.getDate() + 2);
    } else if (ukNow >= closeToday) {      // after close
        label = "Opens [tomorrow in]:";
        target.setDate(target.getDate() + 1);
        if (target.getDay() === 6) {
            label = "Opens [on Monday in]:";
            target.setDate(target.getDate() + 2);
        } else if (target.getDay() === 0) {
            label = "Opens [on Monday in]:";
            target.setDate(target.getDate() + 1);
        }
    } else if (ukNow < openToday) {        // before open
        label = "Opens [today in]:";
    } else {
        return null;                       // market is open
    }

    // Safety: if target is already past, push to next weekday open
    if (target <= ukNow) {
        target.setDate(target.getDate() + 1);
        while (target.getDay() === 0 || target.getDay() === 6) {
            target.setDate(target.getDate() + 1);
        }
        label = "Opens [next in]:";
    }

    return { label, target };
}

function startFtseCountdown(target, labelEl) {
    if (ftseCountdownTimer) clearInterval(ftseCountdownTimer);
    function tick() {
        const diff = target - new Date();
        if (diff <= 0) {
            labelEl.textContent = "Open";
            clearInterval(ftseCountdownTimer);
            return;
        }
        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);
        labelEl.textContent = `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
    }
    tick();
    ftseCountdownTimer = setInterval(tick, 1000);
}

async function updateCacheStatus() {
    try {
        const res = await fetch("/status");
        const data = await res.json();
        const last = data.last_update ? new Date(data.last_update).toLocaleTimeString() : "never";
        document.getElementById("cache-status").textContent =
            `Cache: ${data.symbols || 0} symbols · last update ${last}`;

        const ftse = data.ftse || {};
        const el = document.getElementById("ftse-status");
        const prevText = ftse.previous != null ? formatNumber(ftse.previous, "price") : "—";
        const prevCls = ftse.previous_was_up === true ? "positive" :
                        ftse.previous_was_up === false ? "negative" : "";

        if (ftse.is_open && ftse.current != null) {
            const currText = formatNumber(ftse.current, "price");
            const currCls = ftse.previous != null ? (ftse.current >= ftse.previous ? "positive" : "negative") : "";

            let changeText = "—";
            let changePctText = "—";
            let changeCls = "";

            if (ftse.previous != null && ftse.current != null) {
                const change = ftse.current - ftse.previous;
                const changePct = (change / ftse.previous) * 100;
                changeText = (change >= 0 ? "+" : "") + formatNumber(change, "price");
                changePctText = (changePct >= 0 ? "+" : "") + changePct.toFixed(2) + "%";
                changeCls = change >= 0 ? "positive" : "negative";
            }

            el.innerHTML = `
                FTSE Previous: <span class="${prevCls}">${prevText}</span>
                &nbsp;&nbsp;FTSE Current: <span id="ftse-current" class="${currCls}">${currText}</span>
                &nbsp;&nbsp;Change: <span class="${changeCls}">${changeText}</span>
                &nbsp;&nbsp;Change %: <span class="${changeCls}">${changePctText}</span>
            `;

            if (lastFtseCurrent != null && ftse.current !== lastFtseCurrent) {
                const cell = document.getElementById("ftse-current");
                if (cell) triggerFlash(cell, ftse.current > lastFtseCurrent);
            }
            lastFtseCurrent = ftse.current;
            if (ftseCountdownTimer) clearInterval(ftseCountdownTimer);
        } else {
            const info = nextOpenDescription(ftse.server_time);
            const prevCls = ftse.previous_was_up === true ? "positive" :
                            ftse.previous_was_up === false ? "negative" : "";
            const prevText = ftse.previous != null ? formatNumber(ftse.previous, "price") : "—";

            el.innerHTML = `
                FTSE Previous: <span class="${prevCls}">${prevText}</span>
                &nbsp;&nbsp;FTSE Current: Closed
                ${info ? ` - <span id="ftse-open-label"></span> <span id="ftse-countdown"></span>` : ""}
            `;

            if (info) {
                document.getElementById("ftse-open-label").textContent = info.label;
                startFtseCountdown(info.target, document.getElementById("ftse-countdown"));
            }
        }
    } catch (e) {}
}

window.refreshVisible = async function () {
    // ---------- Tool 8 ----------
    if (document.getElementById("risers-table") && window.Tool8) {
        // Re-fetch the full enriched Tool 8 data
        const body = {
            risers_index: window.AppState.currentRisersIndex || "ALL",
            fallers_index: window.AppState.currentFallersIndex || "ALL",
            limit: parseInt(localStorage.getItem("listLimit") || "25", 10)
        };
        const res = await fetch("/tool/8", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (window.Tool8 && data.result) {
            window.Tool8.render(data.result);
        }
        return;
    }

    // ---------- Tool 7 ----------
    // To become: 'Rules' where Hit Parametes can be set and adjusted.
};

// Re-apply a saved sort only if the visual order has actually changed.
// Avoids unnecessary DOM moves (and therefore flicker) on price ticks.
function reapplySortIfChanged(table, key, dir) {
    if (!table || !key) return;
    const th = table.querySelector(`th[data-key="${key}"]`);
    if (!th) return;

    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const rows = [...tbody.querySelectorAll("tr")];
    if (rows.length < 2) return;

    const colIndex = th.cellIndex;

    const sorted = [...rows].sort((a, b) => {
        let va = a.children[colIndex].textContent.trim();
        let vb = b.children[colIndex].textContent.trim();
        const na = parseFloat(String(va).replace(/[^0-9.-]/g, ""));
        const nb = parseFloat(String(vb).replace(/[^0-9.-]/g, ""));
        if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir;
        return String(va).localeCompare(String(vb)) * dir;
    });

    // Already in the correct order?
    let same = true;
    for (let i = 0; i < rows.length; i++) {
        if (rows[i] !== sorted[i]) {
            same = false;
            break;
        }
    }
    if (same) return;

    // Order changed — move rows
    sorted.forEach(r => tbody.appendChild(r));

    // Update sort indicator
    table.querySelectorAll("th[data-key]").forEach(h => {
        [...h.childNodes].forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
                node.textContent = node.textContent.replace(/ ↑| ↓/, "");
            }
        });
    });
    th.appendChild(document.createTextNode(dir === 1 ? " ↑" : " ↓"));
}

window.formatNumber = formatNumber;
window.tradingViewSymbol = tradingViewSymbol;
window.buildSymbolLink = buildSymbolLink;
window.attachCheckboxListeners = attachCheckboxListeners;
window.makeTableSortable = makeTableSortable;
window.drawSparkline = drawSparkline;
window.triggerFlash = triggerFlash;
window.startAutoRefresh = startAutoRefresh;
window.stopAutoRefresh = stopAutoRefresh;
window.updateCacheStatus = updateCacheStatus;
window.reapplySortIfChanged = reapplySortIfChanged;
window.makeTableSortable = makeTableSortable;

