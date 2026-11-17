// static/js/tool2.js
window.Tool2 = {
    async show() {
        // Pause background + auto-refresh while we are in Tool 2
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
        // Resume background + auto-refresh when leaving Tool 2
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

        // Load current counts
        let counts = {};
        try {
            const cRes = await fetch("/scripts/counts");
            counts = await cRes.json();
        } catch (e) {
            console.warn("Could not load script counts", e);
        }

        // Fetch DESC metadata
        const meta = await Promise.all(files.map(async f => {
            try {
                const r = await fetch(`/scripts/meta?name=${encodeURIComponent(f)}`);
                return await r.json();
            } catch {
                return { name: f, desc: "", run: "" };
            }
        }));

        let buttonsHtml = "";
        meta.forEach(m => {
            const title = m.desc ? m.desc.replace(/"/g, "&quot;") : m.name;
            const used = counts[m.name] || 0;
            buttonsHtml += `
                <button class="script-btn" 
                        data-script="${m.name}" 
                        title="${title}"
                        style="position:relative;">
                    <span class="script-name">${m.name}</span>
                    <span class="run-badge tool2">Used: ${used}</span>
                    <input type="checkbox" class="script-select" data-script="${m.name}"
                           style="position:absolute; bottom:4px; right:4px; width:15px; height:15px; cursor:pointer; z-index:2;"
                           title="Select for deletion">
                </button>`;
        });

        buttonsHtml += `
            <button class="script-btn" id="tool2-refresh" title="Re-scan scripts directory" style="background:#1e5c3a;">
                Refresh
            </button>
            <button class="script-btn" id="tool2-delete" title="Delete selected scripts" style="background:#5c2a2a;">
                Delete
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
                ${buttonsHtml}
            </div>
            <div style="position:relative; margin-top:20px;">
                <button id="tool2-copy" title="Copy all output to clipboard"
                        style="position:absolute; top:8px; right:8px; padding:4px 10px; font-size:0.85rem; background:#1e3a5c; color:#fff; border:none; border-radius:4px; cursor:pointer;">
                    Copy
                </button>
                <pre id="script-output" class="script-output" style="margin-top:0; padding-top:36px;"></pre>
            </div>`;

        // Refresh
        document.getElementById("tool2-refresh").addEventListener("click", () => this.refresh());

        // Delete selected
        document.getElementById("tool2-delete").addEventListener("click", async () => {
            const selected = Array.from(document.querySelectorAll(".script-select:checked"))
                .map(cb => cb.dataset.script);
            if (selected.length === 0) {
                alert("No scripts selected");
                return;
            }
            if (!confirm(`Delete ${selected.length} script(s)?\n\n${selected.join("\n")}`)) {
                return;
            }
            try {
                const res = await fetch("/scripts/delete", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({scripts: selected})
                });
                const data = await res.json();
                if (data.errors && data.errors.length) {
                    alert("Some errors:\n" + data.errors.join("\n"));
                }
                await this.refresh();
            } catch (e) {
                alert("Delete failed: " + e);
            }
        });

        // Cancel → leave Tool 2
        document.getElementById("tool2-cancel").addEventListener("click", async () => {
            await this.hide();
            const dash = document.querySelector('[data-tool="dashboard"]');
            if (dash) dash.click();
            else if (window.Dashboard) window.Dashboard.show();
        });

        // Copy output
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

        // Script buttons → increment count + run
        document.querySelectorAll(".script-btn[data-script]").forEach(btn => {
            btn.addEventListener("click", async (e) => {
                // Ignore clicks that land on the checkbox
                if (e.target.classList.contains("script-select")) return;

                const name = btn.dataset.script;
                const output = document.getElementById("script-output");
                output.textContent = "Running…";

                // Increment count first
                try {
                    await fetch("/scripts/increment", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({script: name})
                    });
                    // Update badge live
                    const badge = btn.querySelector(".run-badge");
                    if (badge) {
                        const current = parseInt(badge.textContent.replace(/\D/g, "")) || 0;
                        badge.textContent = `Used: ${current + 1}`;
                    }
                } catch (e) {
                    console.warn("Could not increment count", e);
                }

                // Run the script
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
                } catch (e) {
                    output.textContent = "Request failed: " + e;
                }
            });
        });
    }
};