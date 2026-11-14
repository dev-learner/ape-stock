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
            </div>`;

        document.getElementById("clear-script-counts").addEventListener("click", async () => {
            if (!confirm("Reset all script run counts to zero?")) return;
            try {
                const res = await fetch("/scripts/clear_counts", {method: "POST"});
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
    }
};