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
                        title="${title}">
                    <span class="script-name">${m.name}</span>
                    <span class="run-badge tool2">Used: ${used}</span>
                </button>`;
        });

        buttonsHtml += `
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
            <pre id="script-output" class="script-output" style="margin-top:20px;"></pre>`;

        // Cancel → leave Tool 2
        document.getElementById("tool2-cancel").addEventListener("click", async () => {
            await this.hide();
            const dash = document.querySelector('[data-tool="dashboard"]');
            if (dash) dash.click();
            else if (window.Dashboard) window.Dashboard.show();
        });

        // Script buttons → increment count + run
        document.querySelectorAll(".script-btn[data-script]").forEach(btn => {
            btn.addEventListener("click", async () => {
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