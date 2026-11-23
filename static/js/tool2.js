// static/js/tool2.js
window.Tool2 = {
    async show() {
        await fetch("/scripts/pause", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({paused: true})
        });
        if (typeof stopAutoRefresh === "function") stopAutoRefresh();

        const res = await fetch("/scripts/list");
        const files = await res.json();
        await this.render(files);
    },

    async hide() {
        await fetch("/scripts/pause", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({paused: false})
        });
        if (typeof startAutoRefresh === "function") startAutoRefresh();
    },

    async refresh() {
        const res = await fetch("/scripts/list");
        const files = await res.json();
        await this.render(files);
    },

    async render(files) {
        const container = document.getElementById("results");

        let counts = {};
        let lastRuns = {};
        try {
            const cRes = await fetch("/scripts/counts");
            counts = await cRes.json();
            const lRes = await fetch("/scripts/last_runs");
            lastRuns = await lRes.json();
        } catch (e) {
            console.warn("Could not load script metadata", e);
        }

        const meta = await Promise.all(files.map(async f => {
            try {
                const r = await fetch(`/scripts/meta?name=${encodeURIComponent(f)}`);
                return await r.json();
            } catch {
                return { name: f, friendly: f, desc: "", detail: "", allow_delete: 0 };
            }
        }));

        let cardsHtml = "";
        meta.forEach(m => {
            const used = counts[m.name] || 0;
            const last = lastRuns[m.name] ? lastRuns[m.name].slice(0, 10) : "Never";
            const protectedClass = m.allow_delete === 0 ? "protected" : "";
            const lock = m.allow_delete === 0 ? '<span class="lock-icon" title="Protected">🔒</span>' : "";
            cardsHtml += `
                <div class="script-card ${protectedClass}" data-script="${m.name}">
                    <div class="script-card-body">
                        <div class="script-name">${m.friendly || m.name}</div>
                        <div class="script-desc">${m.desc || ""}</div>
                        <div class="script-last">Last run: ${last}</div>
                    </div>
                    <span class="run-badge tool2">Used: ${used}</span>
                    <div class="script-actions">
                        <button class="mini-btn script-run" data-script="${m.name}">Run</button>
                        <button class="mini-btn script-delete" data-script="${m.name}" ${m.allow_delete === 0 ? "disabled" : ""}>
                            Delete ${lock}
                        </button>
                    </div>
                </div>`;
        });

        cardsHtml += `
            <button class="script-btn" id="tool2-refresh" title="Re-scan scripts directory" style="background:#1e5c3a; text-align:center; justify-content:center;">
                Refresh
            </button>
            <button class="script-btn cancel-btn" id="tool2-cancel" title="Return to Dashboard">
                Cancel
            </button>`;

        container.innerHTML = `
            <div id="tool2-warning" style="background:#5c2a2a; color:#fff; padding:10px 16px; border-radius:6px; margin-bottom:12px; font-weight:600;">
                ⚠ Tool 2 active — background updates and auto-refresh are paused
            </div>
            <div class="region-bar">
                <h3>Ad-Hoc Scripts</h3>
            </div>
            <div class="script-grid">
                ${cardsHtml}
            </div>
            <div style="position:relative; margin-top:20px;">
                <div style="display:flex; justify-content:flex-end; gap:6px; margin-bottom:6px;">
                    <button id="tool2-copy" title="Copy all output to clipboard"
                            style="padding:4px 10px; font-size:0.85rem; background:#1e3a5c; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                        Copy
                    </button>
                    <button id="tool2-clear" title="Clear output"
                            style="padding:4px 10px; font-size:0.85rem; background:#5c2a2a; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                        Clear
                    </button>
                </div>
                <pre id="script-output" class="script-output" style="margin-top:0;"></pre>
            </div>`;

        // Refresh
        document.getElementById("tool2-refresh").addEventListener("click", () => this.refresh());

        // Cancel
        document.getElementById("tool2-cancel").addEventListener("click", async () => {
            await this.hide();
            const dash = document.querySelector('[data-tool="dashboard"]');
            if (dash) dash.click();
            else if (window.Dashboard) window.Dashboard.show();
        });

        // Copy
        document.getElementById("tool2-copy").addEventListener("click", async () => {
            const output = document.getElementById("script-output");
            const text = output.textContent || "";
            try {
                await navigator.clipboard.writeText(text);
                const btn = document.getElementById("tool2-copy");
                const orig = btn.textContent;
                btn.textContent = "Copied";
                setTimeout(() => { btn.textContent = orig; }, 1500);
            } catch (e) {
                alert("Copy failed");
            }
        });

        // Clear
        document.getElementById("tool2-clear").addEventListener("click", () => {
            document.getElementById("script-output").textContent = "";
        });

        // Card body click → show DETAIL
        document.querySelectorAll(".script-card").forEach(card => {
            card.addEventListener("click", (e) => {
                if (e.target.closest(".script-actions")) return;
                const name = card.dataset.script;
                const m = meta.find(x => x.name === name);
                const output = document.getElementById("script-output");
                output.textContent = m && m.detail ? m.detail : "No extended description available.";
            });
        });

        // Mini Run buttons
        document.querySelectorAll(".script-run").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const name = btn.dataset.script;
                const m = meta.find(x => x.name === name);
                const friendly = m ? (m.friendly || name) : name;
                if (!confirm(`Run ${friendly} Script?`)) return;

                const output = document.getElementById("script-output");
                output.textContent = "Running…";

                try {
                    await fetch("/scripts/increment", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({script: name})
                    });
                    const badge = btn.closest(".script-card").querySelector(".run-badge");
                    if (badge) {
                        const current = parseInt(badge.textContent.replace(/\D/g, "")) || 0;
                        badge.textContent = `Used: ${current + 1}`;
                    }
                } catch (e) {
                    console.warn("Could not increment count", e);
                }

                try {
                    const res = await fetch("/scripts/run", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({script: name})
                    });
                    const data = await res.json();
                    if (data.error) {
                        output.textContent = "Error: " + data.error;
                    } else {
                        output.textContent = (data.stdout || "") + (data.stderr ? "\n--- stderr ---\n" + data.stderr : "");
                    }
                    // Do NOT refresh here — it was clearing the output
                } catch (e) {
                    output.textContent = "Request failed: " + e;
                }
            });
        });

        // Mini Delete buttons
        document.querySelectorAll(".script-delete").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const name = btn.dataset.script;
                const m = meta.find(x => x.name === name);
                const friendly = m ? (m.friendly || name) : name;
                if (m && m.allow_delete === 0) {
                    alert("Deletion NOT allowed!");
                    return;
                }
                if (!confirm(`Delete ${friendly} Script?`)) return;

                try {
                    const res = await fetch("/scripts/delete", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({scripts: [name]})
                    });
                    const data = await res.json();
                    if (data.errors && data.errors.length) {
                        alert("Error:\n" + data.errors.join("\n"));
                    }
                    await this.refresh();
                } catch (e) {
                    alert("Delete failed: " + e);
                }
            });
        });
    }
};