// static/js/tool9.js
window.Tool9 = {
    defaults: {
        listLimit: "25",
        riserPct: "3",
        fallerPct: "3",
        hitThreshold: "50",
        notional: "500",
        stampPct: "0.5",
        tracker_close_target: "3",
        rank_window: "35",
        rank_presence: "50",
        rank_cutoff: "12",
        pe_min: "5",
        pe_max: "40",
        pb_max: "4",
        require_dividend: "0",
        use_valuation: "0",
        cand_rank_max: "12",
        cand_pe_min: "5",
        cand_pe_max: "40",
        cand_pb_max: "4",
        cand_require_div: "0",
        rsiOversold: "30",
        rsiOverbought: "70",
        rsiLength: "7"
    },

    async show() {
        const container = document.getElementById("results");
        container.innerHTML = `
            <div class="settings-page" style="max-width:1100px; margin:0 auto; padding:8px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <h1 style="margin:0;">Settings</h1>
                    <button id="saveBtn" class="mini-btn" style="background:#1e5c3a; padding:8px 16px;">Save Settings</button>
                </div>
                <div id="settings-msg" style="min-height:1.4em; margin-bottom:8px;"></div>

                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px;">

                    <!-- Lists & Thresholds -->
                    <div class="card">
                        <h3>Lists & Thresholds</h3>
                        <label>Limit Lists</label>
                        <select id="listLimit">
                            <option value="5">5</option>
                            <option value="10">10</option>
                            <option value="15">15</option>
                            <option value="20">20</option>
                            <option value="25">25</option>
                            <option value="all">All</option>
                        </select>
                        <label>Riser % threshold</label>
                        <input type="number" id="riserPct" min="0" max="20" step="0.5">
                        <label>Faller % threshold</label>
                        <input type="number" id="fallerPct" min="0" max="20" step="0.5">
                        <label>Hit threshold (%)</label>
                        <input type="number" id="hitThreshold" min="0" max="100" step="5">
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="lists">Restore Defaults</button>
                        </div>
                    </div>

                    <!-- Position & Costs -->
                    <div class="card">
                        <h3>Position & Costs</h3>
                        <label>Default Notional (£)</label>
                        <input type="number" id="notional" min="100" step="50">
                        <label>Stamp Duty (%)</label>
                        <input type="number" id="stampPct" min="0" max="5" step="0.1">
                        <label>Tracker Close Target (%)</label>
                        <input type="number" id="trackerCloseTarget" min="1" max="10" step="0.5">
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="position">Restore Defaults</button>
                        </div>
                    </div>

                    <!-- Ranking -->
                    <div class="card">
                        <h3>Ranking</h3>
                        <label>Persistence window (days)</label>
                        <input type="number" id="rankWindow" min="5" max="120" step="1">
                        <label>Minimum presence (%)</label>
                        <input type="number" id="rankPresence" min="10" max="100" step="1">
                        <label>Rank cut-off</label>
                        <input type="number" id="rankCutoff" min="5" max="50" step="1">
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="ranking">Restore Defaults</button>
                        </div>
                    </div>

                    <!-- Valuation Filters -->
                    <div class="card">
                        <h3>Valuation Filters (Tool 4)</h3>
                        <label style="display:flex; align-items:center; gap:8px;">
                            Use valuation filters <input type="checkbox" id="useValuation">
                        </label>
                        <label>Trailing PE min</label>
                        <input type="number" id="peMin" min="0" max="100" step="0.5">
                        <label>Trailing PE max</label>
                        <input type="number" id="peMax" min="0" max="200" step="0.5">
                        <label>Price / Book max</label>
                        <input type="number" id="pbMax" min="0" max="20" step="0.1">
                        <label>Require positive dividend yield</label>
                        <select id="requireDividend">
                            <option value="1">Yes</option>
                            <option value="0">No</option>
                        </select>
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="valuation">Restore Defaults</button>
                        </div>
                    </div>

                    <!-- Candidates (Tool 7) -->
                    <div class="card">
                        <h3>Candidates (Tool 7)</h3>
                        <label>Rank cut-off (max)</label>
                        <input type="number" id="candRankMax" min="1" max="100" step="1">
                        <label>Trailing PE min</label>
                        <input type="number" id="candPeMin" min="0" max="100" step="0.5">
                        <label>Trailing PE max</label>
                        <input type="number" id="candPeMax" min="0" max="200" step="0.5">
                        <label>Price / Book max</label>
                        <input type="number" id="candPbMax" min="0" max="20" step="0.1">
                        <label>Require positive dividend yield</label>
                        <select id="candRequireDiv">
                            <option value="0">No</option>
                            <option value="1">Yes</option>
                        </select>
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="candidates">Restore Defaults</button>
                        </div>
                    </div>

                    <!-- RSI -->
                    <div class="card">
                        <h3>RSI Settings</h3>
                        <label>Oversold Below</label>
                        <input type="number" id="rsiOversold" min="1" max="50" step="1">
                        <label>Overbought Above</label>
                        <input type="number" id="rsiOverbought" min="50" max="100" step="1">
                        <label>Length</label>
                        <input type="number" id="rsiLength" min="1" max="30" step="1">
                        <div style="text-align:right; margin-top:12px;">
                            <button class="mini-btn restore" data-section="rsi">Restore Defaults</button>
                        </div>
                    </div>

                </div>
            </div>`;

        await this.loadSettings();
        this.bindEvents();
    },

    bindEvents() {
        document.getElementById("saveBtn").onclick = () => this.saveSettings();

        document.querySelectorAll(".restore").forEach(btn => {
            btn.onclick = () => this.restoreSection(btn.dataset.section);
        });
    },

    async loadSettings() {
        try {
            const res = await fetch("/settings/get");
            const s = res.ok ? await res.json() : {};
            const merged = { ...this.defaults, ...s };

            const set = (id, key) => {
                const el = document.getElementById(id);
                if (el && merged[key] != null) el.value = merged[key];
            };

            set("listLimit", "listLimit");
            set("riserPct", "riserPct");
            set("fallerPct", "fallerPct");
            set("hitThreshold", "hitThreshold");
            set("notional", "notional");
            set("stampPct", "stampPct");
            set("trackerCloseTarget", "tracker_close_target");
            set("rankWindow", "rank_window");
            set("rankPresence", "rank_presence");
            set("rankCutoff", "rank_cutoff");
            set("peMin", "pe_min");
            set("peMax", "pe_max");
            set("pbMax", "pb_max");
            set("requireDividend", "require_dividend");
            set("candRankMax", "cand_rank_max");
            set("candPeMin", "cand_pe_min");
            set("candPeMax", "cand_pe_max");
            set("candPbMax", "cand_pb_max");
            set("candRequireDiv", "cand_require_div");
            set("rsiOversold", "rsiOversold");
            set("rsiOverbought", "rsiOverbought");
            set("rsiLength", "rsiLength");

            const useVal = document.getElementById("useValuation");
            if (useVal) useVal.checked = (merged.use_valuation === "1");
        } catch (e) {
            console.warn("Could not load settings", e);
        }
    },

    restoreSection(section) {
        const map = {
            lists: ["listLimit", "riserPct", "fallerPct", "hitThreshold"],
            position: ["notional", "stampPct", "trackerCloseTarget"],
            ranking: ["rankWindow", "rankPresence", "rankCutoff"],
            valuation: ["peMin", "peMax", "pbMax", "requireDividend"],
            candidates: ["candRankMax", "candPeMin", "candPeMax", "candPbMax", "candRequireDiv"],
            rsi: ["rsiOversold", "rsiOverbought", "rsiLength"]
        };
        const keys = map[section] || [];
        keys.forEach(id => {
            const el = document.getElementById(id);
            const key = this.idToKey(id);
            if (el && this.defaults[key] != null) el.value = this.defaults[key];
        });
        if (section === "valuation") {
            document.getElementById("useValuation").checked = (this.defaults.use_valuation === "1");
        }
    },

    idToKey(id) {
        const map = {
            listLimit: "listLimit",
            riserPct: "riserPct",
            fallerPct: "fallerPct",
            hitThreshold: "hitThreshold",
            notional: "notional",
            stampPct: "stampPct",
            trackerCloseTarget: "tracker_close_target",
            rankWindow: "rank_window",
            rankPresence: "rank_presence",
            rankCutoff: "rank_cutoff",
            peMin: "pe_min",
            peMax: "pe_max",
            pbMax: "pb_max",
            requireDividend: "require_dividend",
            candRankMax: "cand_rank_max",
            candPeMin: "cand_pe_min",
            candPeMax: "cand_pe_max",
            candPbMax: "cand_pb_max",
            candRequireDiv: "cand_require_div",
            rsiOversold: "rsiOversold",
            rsiOverbought: "rsiOverbought",
            rsiLength: "rsiLength"
        };
        return map[id] || id;
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
            rank_window: document.getElementById("rankWindow").value,
            rank_presence: document.getElementById("rankPresence").value,
            rank_cutoff: document.getElementById("rankCutoff").value,
            pe_min: document.getElementById("peMin").value,
            pe_max: document.getElementById("peMax").value,
            pb_max: document.getElementById("pbMax").value,
            require_dividend: document.getElementById("requireDividend").value,
            use_valuation: document.getElementById("useValuation").checked ? "1" : "0",
            cand_rank_max: document.getElementById("candRankMax").value,
            cand_pe_min: document.getElementById("candPeMin").value,
            cand_pe_max: document.getElementById("candPeMax").value,
            cand_pb_max: document.getElementById("candPbMax").value,
            cand_require_div: document.getElementById("candRequireDiv").value,
            rsiOversold: document.getElementById("rsiOversold").value,
            rsiOverbought: document.getElementById("rsiOverbought").value,
            rsiLength: document.getElementById("rsiLength").value
        };

        try {
            const res = await fetch("/settings/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const msg = document.getElementById("settings-msg");
            if (res.ok) {
                Object.keys(payload).forEach(k => localStorage.setItem(k, payload[k]));
                msg.textContent = "Settings saved";
                msg.style.color = "#4ade80";
                msg.style.fontWeight = "600";
            } else {
                msg.textContent = "Save failed";
                msg.style.color = "#f87171";
            }
            setTimeout(() => { msg.textContent = ""; }, 1800);
        } catch (e) {
            document.getElementById("settings-msg").textContent = "Save error";
        }
    }
};