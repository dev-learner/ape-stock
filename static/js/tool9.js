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

                <h2 style="margin:28px 0 12px; color:#7fdbff; font-size:1.15rem;">Ranking</h2>

                <label for="rankWindow">Persistence window (days)</label>
                <input type="number" id="rankWindow" min="5" max="120" step="1" value="35">

                <label for="rankPresence">Minimum presence (%)</label>
                <input type="number" id="rankPresence" min="10" max="100" step="1" value="50">

                <label for="rankCutoff">Rank cut-off</label>
                <input type="number" id="rankCutoff" min="5" max="50" step="1" value="12">

                <h2 style="margin:28px 0 12px; color:#7fdbff; font-size:1.15rem;">
                    Valuation Filters (Tool 4)
                    <label style="font-size:0.95rem; font-weight:normal; margin-left:16px; color:#ddd; display:inline-flex; align-items:center; gap:6px;">
                        Use? <input type="checkbox" id="useValuation" style="margin:0; width:16px; height:16px;">
                    </label>
                </h2>

                <label for="peMin">Trailing PE min</label>
                <input type="number" id="peMin" min="0" max="100" step="0.5" value="5">

                <label for="peMax">Trailing PE max</label>
                <input type="number" id="peMax" min="0" max="200" step="0.5" value="40">

                <label for="pbMax">Price / Book max</label>
                <input type="number" id="pbMax" min="0" max="20" step="0.1" value="4">

                <label for="requireDividend">Require positive dividend yield</label>
                <select id="requireDividend">
                    <option value="1">Yes</option>
                    <option value="0">No</option>
                </select>

                <h2 style="margin:28px 0 12px; color:#7fdbff; font-size:1.15rem;">Candidate Selection</h2>

                <label for="candRank">Rank cut-off (Buy / Hold)</label>
                <input type="number" id="candRank" min="1" max="100" step="1" value="12">

                <label for="candRequireFaller">Require faller for Buy</label>
                <select id="candRequireFaller">
                    <option value="1">Yes</option>
                    <option value="0">No</option>
                </select>

                <label for="candVs50Buy">vs 50MA min for Buy</label>
                <input type="number" id="candVs50Buy" min="-50" max="50" step="0.1" value="0">

                <label for="candVs200Buy">vs 200MA min for Buy</label>
                <input type="number" id="candVs200Buy" min="-50" max="50" step="0.1" value="0">

                <label for="candVs50Hold">vs 50MA min for Hold</label>
                <input type="number" id="candVs50Hold" min="-50" max="50" step="0.1" value="0">

                <label for="candVs50Sell">vs 50MA max for Sell</label>
                <input type="number" id="candVs50Sell" min="-50" max="50" step="0.1" value="0">

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
            set("rankWindow", "rank_window");
            set("rankPresence", "rank_presence");
            set("rankCutoff", "rank_cutoff");
            set("peMin", "pe_min");
            set("peMax", "pe_max");
            set("pbMax", "pb_max");
            set("requireDividend", "require_dividend");
            set("candRank", "cand_rank");
            set("candRequireFaller", "cand_require_faller");
            set("candVs50Buy", "cand_vs50_buy");
            set("candVs200Buy", "cand_vs200_buy");
            set("candVs50Hold", "cand_vs50_hold");
            set("candVs50Sell", "cand_vs50_sell");

            if (s.use_valuation != null) {
                document.getElementById("useValuation").checked = (s.use_valuation === "1");
            }

            // Keep localStorage in sync
            if (s.listLimit) localStorage.setItem("listLimit", s.listLimit);
            if (s.riserPct) localStorage.setItem("riserPct", s.riserPct);
            if (s.fallerPct) localStorage.setItem("fallerPct", s.fallerPct);
            if (s.hitThreshold) localStorage.setItem("hitThreshold", s.hitThreshold);
            if (s.notional) localStorage.setItem("notional", s.notional);
            if (s.stampPct) localStorage.setItem("stampPct", s.stampPct);
            if (s.rsiOversold) localStorage.setItem("rsiOversold", s.rsiOversold);
            if (s.rsiOverbought) localStorage.setItem("rsiOverbought", s.rsiOverbought);
            if (s.rsiLength) localStorage.setItem("rsiLength", s.rsiLength);
            if (s.rank_window) localStorage.setItem("rank_window", s.rank_window);
            if (s.rank_presence) localStorage.setItem("rank_presence", s.rank_presence);
            if (s.rank_cutoff) localStorage.setItem("rank_cutoff", s.rank_cutoff);
            if (s.pe_min) localStorage.setItem("pe_min", s.pe_min);
            if (s.pe_max) localStorage.setItem("pe_max", s.pe_max);
            if (s.pb_max) localStorage.setItem("pb_max", s.pb_max);
            if (s.require_dividend) localStorage.setItem("require_dividend", s.require_dividend);
            if (s.use_valuation) localStorage.setItem("use_valuation", s.use_valuation);
            if (s.cand_rank) localStorage.setItem("cand_rank", s.cand_rank);
            if (s.cand_require_faller) localStorage.setItem("cand_require_faller", s.cand_require_faller);
            if (s.cand_vs50_buy) localStorage.setItem("cand_vs50_buy", s.cand_vs50_buy);
            if (s.cand_vs200_buy) localStorage.setItem("cand_vs200_buy", s.cand_vs200_buy);
            if (s.cand_vs50_hold) localStorage.setItem("cand_vs50_hold", s.cand_vs50_hold);
            if (s.cand_vs50_sell) localStorage.setItem("cand_vs50_sell", s.cand_vs50_sell);
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
            rsiLength: document.getElementById("rsiLength").value,
            rank_window: document.getElementById("rankWindow").value,
            rank_presence: document.getElementById("rankPresence").value,
            rank_cutoff: document.getElementById("rankCutoff").value,
            pe_min: document.getElementById("peMin").value,
            pe_max: document.getElementById("peMax").value,
            pb_max: document.getElementById("pbMax").value,
            require_dividend: document.getElementById("requireDividend").value,
            use_valuation: document.getElementById("useValuation").checked ? "1" : "0",
            cand_rank: document.getElementById("candRank").value,
            cand_require_faller: document.getElementById("candRequireFaller").value,
            cand_vs50_buy: document.getElementById("candVs50Buy").value,
            cand_vs200_buy: document.getElementById("candVs200Buy").value,
            cand_vs50_hold: document.getElementById("candVs50Hold").value,
            cand_vs50_sell: document.getElementById("candVs50Sell").value
        };

        try {
            const res = await fetch("/settings/save", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const msg = document.getElementById("settings-msg");
            if (res.ok) {
                Object.keys(payload).forEach(k => localStorage.setItem(k, payload[k]));
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