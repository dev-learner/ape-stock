// static/js/tool2.js
window.Tool2 = {
    async show() {
        const res = await fetch("/scripts/list");
        const files = await res.json();
        this.render(files);
    },

    async render(files) {
        const container = document.getElementById("results");
        let listHtml = "";

        if (!files.length) {
            listHtml = "<p>No scripts found in /scripts.</p>";
        } else {
            // Fetch DESC / RUN for each script
            const meta = await Promise.all(files.map(async f => {
                try {
                    const r = await fetch(`/scripts/meta?name=${encodeURIComponent(f)}`);
                    return await r.json();
                } catch {
                    return { name: f, desc: "", run: "" };
                }
            }));

            listHtml = `<ul class="script-list">`;
            meta.forEach(m => {
                const badge = m.run === "VENV"
                    ? `<span class="run-badge venv">VENV</span>`
                    : `<span class="run-badge tool2">Tool2</span>`;
                const desc = m.desc ? `<div class="script-desc">${m.desc}</div>` : "";
                listHtml += `<li>
                    <label>
                        <input type="radio" name="script-choice" value="${m.name}">
                        <strong>${m.name}</strong> ${badge}
                        ${desc}
                    </label>
                </li>`;
            });
            listHtml += `</ul>`;
        }

        container.innerHTML = `
            <div class="region-bar">
                <h3>Ad-Hoc Scripts</h3>
                <div class="right-controls">
                    <button class="mini-btn" id="script-cancel">Cancel</button>
                    <button class="mini-btn" id="script-run">Run</button>
                </div>
            </div>
            <div id="script-list-area">${listHtml}</div>
            <pre id="script-output" class="script-output"></pre>`;

        document.getElementById("script-cancel").addEventListener("click", () => {
            const dash = document.querySelector('[data-tool="dashboard"]') ||
                         document.querySelector('a[href="/"]') ||
                         document.querySelector('button[data-tool="1"]');
            if (dash) dash.click();
            else if (window.Dashboard) window.Dashboard.show();
        });

        document.getElementById("script-run").addEventListener("click", async () => {
            const selected = document.querySelector('input[name="script-choice"]:checked');
            if (!selected) {
                alert("Select a script first");
                return;
            }

            const output = document.getElementById("script-output");
            const name = selected.value;

            // Check run mode first
            try {
                const metaRes = await fetch(`/scripts/meta?name=${encodeURIComponent(name)}`);
                const meta = await metaRes.json();
                if (meta.run && meta.run.toUpperCase() === "VENV") {
                    output.textContent = `This script must be run externally.\n\n` +
                                        `Open a terminal, activate the venv, and run:\n` +
                                        `python scripts/${name}`;
                    return;
                }
            } catch (e) {
                // if meta fails, continue and let the backend decide
            }

            output.textContent = "Running…";
            try {
                const res = await fetch("/scripts/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ script: name })
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
    }
};