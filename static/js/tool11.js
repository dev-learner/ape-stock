// static/js/tool11.js
window.Tool11 = {
    async show() {
        const res = await fetch("/grokit/list");
        const files = await res.json();
        await this.render(files);
    },

    async refresh() {
        const res = await fetch("/grokit/list");
        const files = await res.json();
        await this.render(files);
    },

    async render(files) {
        const container = document.getElementById("results");

        let counts = {};
        let lastRuns = {};
        try {
            const cRes = await fetch("/grokit/counts");
            counts = await cRes.json();
            const lRes = await fetch("/grokit/last_runs");
            lastRuns = await lRes.json();
        } catch (e) {
            console.warn("Could not load grokit metadata", e);
        }

        const meta = await Promise.all(files.map(async f => {
            try {
                const r = await fetch(`/grokit/meta?name=${encodeURIComponent(f)}`);
                return await r.json();
            } catch {
                return { name: f, friendly: f, desc: "", detail: "", allow_delete: 1 };
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

        container.innerHTML = `
            <div class="region-bar">
                <h3>Grok-It!</h3>
            </div>
            <div class="script-grid">
                ${cardsHtml}
            </div>
            <div style="margin-top:20px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div style="display:flex; gap:6px;">
                        <button id="tool11-refresh" style="padding:4px 10px; font-size:0.85rem; background:#1e5c3a; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                            Refresh
                        </button>
                        <button id="tool11-cancel" style="padding:4px 10px; font-size:0.85rem; background:#5c2a2a; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                            Cancel
                        </button>
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button id="tool11-copy" style="padding:4px 10px; font-size:0.85rem; background:#1e3a5c; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                            Copy
                        </button>
                        <button id="tool11-clear" style="padding:4px 10px; font-size:0.85rem; background:#5c2a2a; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                            Clear
                        </button>
                    </div>
                </div>
                <pre id="grokit-output" class="script-output" style="margin-top:0;"></pre>
            </div>`;

        document.getElementById("tool11-refresh").addEventListener("click", () => this.refresh());

        document.getElementById("tool11-cancel").addEventListener("click", () => {
            window.AppState.currentTool = "dashboard";
            if (window.Dashboard) window.Dashboard.show();
        });

        document.getElementById("tool11-copy").addEventListener("click", async () => {
            const output = document.getElementById("grokit-output");
            try {
                await navigator.clipboard.writeText(output.textContent || "");
                const btn = document.getElementById("tool11-copy");
                const orig = btn.textContent;
                btn.textContent = "Copied";
                setTimeout(() => { btn.textContent = orig; }, 1500);
            } catch (e) {
                alert("Copy failed");
            }
        });

        document.getElementById("tool11-clear").addEventListener("click", () => {
            document.getElementById("grokit-output").textContent = "";
        });

        document.querySelectorAll(".script-card").forEach(card => {
            card.addEventListener("click", (e) => {
                if (e.target.closest(".script-actions")) return;
                const name = card.dataset.script;
                const m = meta.find(x => x.name === name);
                document.getElementById("grokit-output").textContent =
                    m && m.detail ? m.detail : "No extended description available.";
            });
        });

        document.querySelectorAll(".script-run").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                e.stopPropagation();
                const name = btn.dataset.script;
                const m = meta.find(x => x.name === name);
                const friendly = m ? (m.friendly || name) : name;
                if (!confirm(`Run ${friendly}?`)) return;

                const output = document.getElementById("grokit-output");
                output.textContent = "Running…";

                try {
                    await fetch("/grokit/increment", {
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
                    const res = await fetch("/grokit/run", {
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
                } catch (e) {
                    output.textContent = "Request failed: " + e;
                }
            });
        });

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
                if (!confirm(`Delete ${friendly}?`)) return;

                try {
                    const res = await fetch("/grokit/delete", {
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