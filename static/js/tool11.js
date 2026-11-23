// static/js/tool11.js
// Placeholder for Tool 11 — Grok-It!
// Will later list templates from the grokit/ directory and run them.

window.Tool11 = {
    show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="card" style="max-width:720px; margin:24px auto;">
                <h3>Grok-It!</h3>
                <div class="section">
                    <p style="margin:12px 0 20px; line-height:1.5;">
                        Tool 11 is ready.<br>
                        Templates will live in the <code>grokit/</code> directory.<br>
                        Full list → select → run flow coming next.
                    </p>
                    <button id="tool11-cancel" class="mini-btn" style="background:#5c2a2a;">
                        Back to Dashboard
                    </button>
                </div>
            </div>
        `;

        document.getElementById("tool11-cancel").addEventListener("click", () => {
            window.AppState.currentTool = "dashboard";
            if (window.Dashboard) window.Dashboard.show();
        });
    }
};