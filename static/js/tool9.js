// static/js/tool9.js
window.Tool9 = {
    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="settings-container" style="max-width:640px; margin:0 auto; padding:8px 0;">
                <h1>Settings</h1>

                <label for="listLimit">Limit Lists</label>
                <select id="listLimit">
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="15">15</option>
                    <option value="20">20</option>
                    <option value="25">25</option>
                    <option value="all">All</option>
                </select>

                <label for="riserPct">Riser % threshold</label>
                <input type="number" id="riserPct" min="0" max="20" step="0.5" value="3">

                <label for="fallerPct">Faller % threshold</label>
                <input type="number" id="fallerPct" min="0" max="20" step="0.5" value="3">

                <label for="hitThreshold">Hit threshold (%)</label>
                <input type="number" id="hitThreshold" min="0" max="100" step="5" value="50">

                <label for="notional">Default Notional (£)</label>
                <input type="number" id="notional" min="100" step="50" value="500">

                <label for="stampPct">Stamp Duty (%)</label>
                <input type="number" id="stampPct" min="0" max="5" step="0.1" value="0.5">

                <label for="trackerCloseTarget">Tracker Close Target (%)</label>
                <input type="number" id="trackerCloseTarget" min="1" max="10" step="0.5" value="3">

                <h2 style="margin:28px 0 12px; color:#7fdbff; font-size:1.15rem;">RSI Settings</h2>

                <label for="rsiOversold">Oversold Below</label>
                <input type="number" id="rsiOversold" min="1" max="50" step="1" value="30">

                <label for="rsiOverbought">Overbought Above</label>
                <input type="number" id="rsiOverbought" min="50" max="100" step="1" value="70">

                <label for="rsiLength">Length</label>
                <input type="number" id="rsiLength" min="1" max="30" step="1" value="7">

                <button id="saveBtn">Save Settings</button>
                <div id="settings-msg"></div>
            </div>`;

        await this.loadSettings();

        document.getElementById("saveBtn").addEventListener("click", () => this.saveSettings());
    },

    async loadSettings() {
        try {
            const res = await fetch("/settings/get");
            if (!res.ok) return;
            const s = await res.json();

            const set = (id, key) => {
                if (s[key] != null) {
                    const el = document.getElementById(id);
                    if (el) el.value = s[key];
                }
            };

            set("listLimit", "listLimit");
            set("riserPct", "riserPct");
            set("fallerPct", "fallerPct");
            set("hitThreshold", "hitThreshold");
            set("notional", "notional");
            set("stampPct", "stampPct");
            set("trackerCloseTarget", "tracker_close_target");
            set("rsiOversold", "rsiOversold");
            set("rsiOverbought", "rsiOverbought");
            set("rsiLength", "rsiLength");

            // Keep localStorage in sync for Tool 8 etc.
            if (s.listLimit) localStorage.setItem("listLimit", s.listLimit);
            if (s.riserPct) localStorage.setItem("riserPct", s.riserPct);
            if (s.fallerPct) localStorage.setItem("fallerPct", s.fallerPct);
            if (s.hitThreshold) localStorage.setItem("hitThreshold", s.hitThreshold);
            if (s.notional) localStorage.setItem("notional", s.notional);
            if (s.stampPct) localStorage.setItem("stampPct", s.stampPct);
            if (s.rsiOversold) localStorage.setItem("rsiOversold", s.rsiOversold);
            if (s.rsiOverbought) localStorage.setItem("rsiOverbought", s.rsiOverbought);
            if (s.rsiLength) localStorage.setItem("rsiLength", s.rsiLength);
        } catch (e) {
            console.warn("Could not load settings", e);
        }
    },

    async saveSettings() {
        const payload = {
            listLimit: document.getElementById("listLimit").value,
            riserPct: document.getElementById("riserPct").value,
            fallerPct: document.getElementById("fallerPct").value,
            hitThreshold: document.getElementById("hitThreshold").value,
            notional: document.getElementById("notional").value,
            stampPct: document.getElementById("stampPct").value,
            tracker_close_target: document.getElementById("trackerCloseTarget").value,
            rsiOversold: document.getElementById("rsiOversold").value,
            rsiOverbought: document.getElementById("rsiOverbought").value,
            rsiLength: document.getElementById("rsiLength").value
        };

        try {
            const res = await fetch("/settings/save", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const msg = document.getElementById("settings-msg");
            if (res.ok) {
                localStorage.setItem("listLimit", payload.listLimit);
                localStorage.setItem("riserPct", payload.riserPct);
                localStorage.setItem("fallerPct", payload.fallerPct);
                localStorage.setItem("hitThreshold", payload.hitThreshold);
                localStorage.setItem("notional", payload.notional);
                localStorage.setItem("stampPct", payload.stampPct);
                localStorage.setItem("rsiOversold", payload.rsiOversold);
                localStorage.setItem("rsiOverbought", payload.rsiOverbought);
                localStorage.setItem("rsiLength", payload.rsiLength);                

                msg.textContent = "Settings saved";
                msg.style.color = "#4ade80";
            } else {
                msg.textContent = "Save failed";
                msg.style.color = "#f87171";
            }
            setTimeout(() => { msg.textContent = ""; }, 2000);
        } catch (e) {
            document.getElementById("settings-msg").textContent = "Save error";
        }
    }
};