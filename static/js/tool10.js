// static/js/tool10.js
window.Tool10 = {
    show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="card" style="max-width:640px; margin:20px auto;">
                <h3>Admin</h3>
                <div class="section">
                    <p>Admin tools (backup, restore, export, import, etc.) will live here.</p>
                    <div style="margin-top:20px;">
                        <button id="clear-script-counts" class="mini-btn" style="background:#5c2a2a;">
                            Clear Script Count
                        </button>
                        <div id="admin-msg" style="margin-top:10px; min-height:1.2em;"></div>
                    </div>
                </div>
            </div>

            <div class="card" style="max-width:480px; margin:16px auto;">
                <h3>Create Bug Report</h3>
                <div style="display:flex; gap:8px; margin-top:12px; flex-wrap:wrap;">
                    <button id="bug-report" class="mini-btn" style="background:#1e5c3a;">Report</button>
                    <button id="bug-generate" class="mini-btn" style="background:#1e3a5c;">Generate</button>
                    <button id="bug-signoff" class="mini-btn" style="background:#1e3a5c;">Sign off</button>
                    <button id="bug-cancel" class="mini-btn" style="background:#5c2a2a;">Cancel</button>
                </div>
            </div>
        `;

        document.getElementById("clear-script-counts").addEventListener("click", async () => {
            if (!confirm("Reset all script run counts to zero?")) return;
            try {
                const res = await fetch("/scripts/clear_counts", { method: "POST" });
                const msg = document.getElementById("admin-msg");
                if (res.ok) {
                    msg.textContent = "Script counts cleared";
                    msg.style.color = "#4ade80";
                } else {
                    msg.textContent = "Clear failed";
                    msg.style.color = "#f87171";
                }
                setTimeout(() => { msg.textContent = ""; }, 2500);
            } catch (e) {
                document.getElementById("admin-msg").textContent = "Error: " + e;
            }
        });

        document.getElementById("bug-report").onclick = () => this.openReportModal();
        document.getElementById("bug-generate").onclick = () => this.openGenerateModal();
        document.getElementById("bug-signoff").onclick = () => this.openSignOffModal();
        document.getElementById("bug-cancel").onclick = () => {
            window.AppState.currentTool = "dashboard";
            if (window.Dashboard) window.Dashboard.show();
        };
    },

    openReportModal() {
        const modal = document.createElement("div");
        modal.className = "modal-overlay active";
        modal.innerHTML = `
            <div class="modal-box">
                <h3>Report Bug</h3>
                <label>Description<br><textarea id="bug-desc" rows="3" style="width:100%"></textarea></label><br><br>
                <label>Expected behaviour<br><textarea id="bug-exp" rows="3" style="width:100%"></textarea></label><br><br>
                <label>Tool<br><input id="bug-tool" style="width:100%"></label><br><br>
                <div class="modal-actions">
                    <button id="bug-save" class="mini-btn" style="background:#1e5c3a;">Save</button>
                    <button id="bug-close" class="mini-btn">Cancel</button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        modal.querySelector("#bug-save").onclick = async () => {
            await fetch("/admin/bugs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    description: document.getElementById("bug-desc").value,
                    expected: document.getElementById("bug-exp").value,
                    tool: document.getElementById("bug-tool").value
                })
            });
            modal.remove();
            this.show();
        };
        modal.querySelector("#bug-close").onclick = () => modal.remove();
    },

    async openGenerateModal() {
        const res = await fetch("/admin/bugs");
        const bugs = await res.json();
        if (!bugs.length) {
            this.flash("No bugs to report!");
            return;
        }

        const promptRes = await fetch("/admin/bugs/prompt");
        const data = await promptRes.json();

        const modal = document.createElement("div");
        modal.className = "modal-overlay active";
        modal.innerHTML = `
            <div class="modal-box">
                <h3>Bug Report Prompt</h3>
                <label>Prompt:<br>
                    <textarea id="bug-prompt" rows="16" style="width:100%; font-family:monospace;">${data.prompt}</textarea>
                </label><br>
                <div class="modal-actions">
                    <button id="bug-copy" class="mini-btn" style="background:#1e3a5c;">Copy</button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        modal.querySelector("#bug-copy").onclick = () => {
            const ta = document.getElementById("bug-prompt");
            ta.select();
            navigator.clipboard.writeText(ta.value);
            modal.remove();
        };
    },

    flash(msg) {
        const el = document.createElement("div");
        el.textContent = msg;
        el.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); background:#1e3a5c; color:white; padding:10px 20px; border-radius:6px; z-index:2000; font-size:0.95rem;";
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 1800);
    },

    async openSignOffModal() {
        const res = await fetch("/admin/bugs");
        const bugs = await res.json();

        const modal = document.createElement("div");
        modal.className = "modal-overlay active";

        const list = bugs.length
            ? bugs.map(b => `
                <label style="display:flex; gap:8px; align-items:flex-start; margin:6px 0;">
                    <input type="checkbox" class="bug-check" data-id="${b.id}">
                    <span><strong>#${b.id}</strong> [${b.tool || "—"}] ${b.description}</span>
                </label>`).join("")
            : "<p>No open bugs.</p>";

        modal.innerHTML = `
            <div class="modal-box">
                <h3>Sign off bugs</h3>
                <div style="max-height:50vh; overflow-y:auto; margin:8px 0;">${list}</div>
                <div class="modal-actions">
                    <button id="bug-signoff-save" class="mini-btn" style="background:#1e5c3a;">Mark complete</button>
                    <button id="bug-signoff-close" class="mini-btn">Cancel</button>
                </div>
            </div>`;
        document.body.appendChild(modal);

        modal.querySelector("#bug-signoff-save").onclick = async () => {
            const ids = [...modal.querySelectorAll(".bug-check:checked")].map(cb => cb.dataset.id);
            if (ids.length) {
                await fetch("/admin/bugs/signoff", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ids })
                });
            }
            modal.remove();
            this.show();
        };
        modal.querySelector("#bug-signoff-close").onclick = () => modal.remove();
    }
};