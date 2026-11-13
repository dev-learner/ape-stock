// static/js/tool7.js
window.Tool7 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="region-bar">
                <h3>Rules</h3>
                <div class="right-controls">
                    <span style="font-size:0.85rem; color:var(--accent);">Hard-coded values (will become editable)</span>
                </div>
            </div>
            <div style="padding:16px 8px; max-width:720px;">
                <p style="color:#aaa; margin-top:0;">
                    These are the values currently baked into the code. 
                    They will be moved here so the Screener, Hit score and Tracker can read them from one place.
                </p>

                <h4 style="margin:20px 0 8px; color:#7fdbff;">Hit / Faller rules</h4>
                <table class="data-table" style="width:100%;">
                    <thead><tr><th>Parameter</th><th>Current value</th><th>Used for</th></tr></thead>
                    <tbody>
                        <tr><td>Min |change %|</td><td>5</td><td>Hit point</td></tr>
                        <tr><td>£ impact threshold</td><td>20,000,000</td><td>Hit point</td></tr>
                        <tr><td>Volume ratio</td><td>1.5</td><td>Hit point</td></tr>
                        <tr><td>RSI(7) oversold</td><td>≤ 30</td><td>Hit point (fallers)</td></tr>
                        <tr><td>Hit % required</td><td>50</td><td>Qualification</td></tr>
                    </tbody>
                </table>

                <h4 style="margin:24px 0 8px; color:#7fdbff;">Tracker</h4>
                <table class="data-table" style="width:100%;">
                    <thead><tr><th>Parameter</th><th>Current value</th><th>Used for</th></tr></thead>
                    <tbody>
                        <tr><td>Close target</td><td>3 %</td><td>Auto-sell</td></tr>
                        <tr><td>Stamp duty</td><td>0.5 %</td><td>Net £ calc</td></tr>
                        <tr><td>Default notional</td><td>£500</td><td>New positions</td></tr>
                    </tbody>
                </table>

                <h4 style="margin:24px 0 8px; color:#7fdbff;">Screener / Safe-bet (planned)</h4>
                <table class="data-table" style="width:100%;">
                    <thead><tr><th>Parameter</th><th>Proposed default</th><th>Notes</th></tr></thead>
                    <tbody>
                        <tr><td>Min market cap / index</td><td>FTSE 100 preferred</td><td>Size / liquidity floor</td></tr>
                        <tr><td>Trend filter</td><td>Above 50-day &amp; 200-day MA</td><td>Avoid multi-month downtrends</td></tr>
                        <tr><td>3-month return floor</td><td>&gt; –15 %</td><td>Not in free-fall</td></tr>
                        <tr><td>Avg volume floor</td><td>Adequate for size</td><td>Practical fills</td></tr>
                        <tr><td>Max distance from 52w high</td><td>Optional</td><td>Leadership filter</td></tr>
                    </tbody>
                </table>

                <p style="margin-top:24px; color:#888; font-size:0.9rem;">
                    Next step: turn the tables above into editable inputs that write to <code>app_settings</code> 
                    (or a dedicated rules table). Screener and Hit logic will then read from there instead of constants.
                </p>
            </div>
        `;
    }
};