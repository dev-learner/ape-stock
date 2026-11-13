window.Tool6 = {
    show() {
        document.getElementById("results").innerHTML = `
            <div class="dashboard-overview">
                <h2>Tool 6 — Insights</h2>
                <p style="color: var(--accent);">Reversal / continuation analysis and fundamentals (coming next)</p>
                <div class="overview-card">
                    <h3>Planned</h3>
                    <ul>
                        <li>Visual % of risers that reverse within 1 h / by close</li>
                        <li>Average give-back / continuation</li>
                        <li>P/E, dividend yield and other fundamentals</li>
                        <li>Drill-down into contributing symbols</li>
                    </ul>
                </div>
            </div>`;
    }
};