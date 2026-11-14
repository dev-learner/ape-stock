// static/js/tool2.js
window.Tool2 = {
    async show() {
        const res = await fetch("/scripts/list");
        const files = await res.json();
        this.render(files);
    },

    async render(files) {
        const container = document.getElementById("results");

        // Fetch DESC metadata for every script
        const meta = await Promise.all(files.map(async f => {
            try {
                const r = await fetch(`/scripts/meta?name=${encodeURIComponent(f)}`);
                return await r.json();
            } catch {
                return { name: f, desc: "", run: "" };
            }
        }));

        // Build grid of script buttons
        // Usage count is currently hard-coded to 0; will be replaced by real persistence later
        let buttonsHtml = "";
        meta.forEach(m => {
            const title = m.desc ? m.desc.replace(/"/g, "&quot;") : m.name;
            const used = 0;   // placeholder – later loaded from storage / DB
            buttonsHtml += `
                <button class="script-btn" 
                        data-script="${m.name}" 
                        title="${title}">
                    <span class="script-name">${m.name}</span>
                    <span class="run-badge tool2">Used: ${used}</span>
                </button>`;
        });

        // Cancel button (returns to Dashboard)
        buttonsHtml += `
            <button class="script-btn cancel-btn" id="tool2-cancel" title="Return to Dashboard">
                Cancel
            </button>`;

        container.innerHTML = `
            <div class="region-bar">
                <h3>Ad-Hoc Scripts</h3>
            </div>
            <div class="script-grid">
                ${buttonsHtml}
            </div>
            <pre id="script-output" class="script-output" style="margin-top:20px;"></pre>`;

        // Cancel → back to Dashboard (Tool 1)
        document.getElementById("tool2-cancel").addEventListener("click", () => {
            const dash = document.querySelector('[data-tool="dashboard"]');
            if (dash) dash.click();
            else if (window.Dashboard) window.Dashboard.show();
        });

        // NOTE: script button on-click handlers intentionally omitted for now
        // so we can review the layout first.
    }
};