// static/js/tool10.js
window.Tool10 = {
    show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="card" style="max-width:640px; margin:20px auto;">
                <h3>Admin</h3>
                <div class="section">
                    <p>Admin tools (backup, restore, export, import, reset script counts, etc.) will live here.</p>
                    <p style="color:#fbbf24; margin-top:12px;">Coming soon.</p>
                </div>
            </div>`;
    }
};