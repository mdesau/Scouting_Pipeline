/* =============================================================================
   WCWAA Scout — front-end logic (app.js)
   -----------------------------------------------------------------------------
   Talks to the local Flask server (server.py). Plain vanilla JS, no build step
   and no dependencies, so the file runs anywhere — including straight from
   Google Drive — without tooling.

   ONLINE vs. VIEW-ONLY
   ────────────────────
   On load we ping /api/divisions. If it answers, the local server is running
   and the full Build / Add-Team controls are enabled. If it does NOT answer
   (e.g. this page was opened on a phone where no Mac server exists), we flip
   into a friendly "view-only" mode so the user is never offered a button that
   could not possibly work.
   ============================================================================ */

"use strict";

// Cache frequently used elements once.
const el = (id) => document.getElementById(id);
const connStatus   = el("connStatus");
const offlineBanner = el("offlineBanner");

let SERVER_ONLINE = false;   // set by checkConnection()
let activeStream  = null;    // current EventSource for a running build

// ── Tab switching ───────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
    el("tab-" + tab).classList.remove("hidden");
    // Lazily load reports the first time that tab is opened.
    if (tab === "reports") loadReports();
  });
});

// ── Connection check ─────────────────────────────────────────────────────────
/**
 * Ping the server. Updates the status dot and toggles view-only mode.
 * Returns the parsed /api/divisions payload when online, else null.
 */
async function checkConnection() {
  try {
    const res = await fetch("/api/divisions", { cache: "no-store" });
    if (!res.ok) throw new Error("bad status");
    const data = await res.json();
    SERVER_ONLINE = true;
    setStatus(true);
    return data;
  } catch (_e) {
    SERVER_ONLINE = false;
    setStatus(false);
    return null;
  }
}

function setStatus(online) {
  connStatus.classList.toggle("online", online);
  connStatus.classList.toggle("offline", !online);
  connStatus.querySelector(".txt").textContent = online ? "Server online" : "View-only";
  offlineBanner.classList.toggle("hidden", online);
  // Disable build/add/season controls when the engine is unreachable.
  ["buildBtn", "addBtn", "buildSeason", "buildDivision", "buildTeam",
   "addSeason", "addUrl", "addDivision", "addFolder",
   "createSeasonBtn", "newSeasonId", "newSeasonDisplay",
   "newMajorsId", "newMinorsId", "newSetActive"]
    .forEach((id) => { const n = el(id); if (n) n.disabled = !online; });
}

// ── Build tab ────────────────────────────────────────────────────────────────
const buildDivision = el("buildDivision");
const buildTeam     = el("buildTeam");
let DIVISIONS = [];   // [{name, type, teams:[...]}, ...]

/** Populate the division dropdown and wire the team dropdown to follow it. */
function populateDivisions(data) {
  DIVISIONS = data.divisions;
  buildDivision.innerHTML = '<option value="">All divisions</option>';
  DIVISIONS.forEach((d) => {
    const o = document.createElement("option");
    o.value = d.name;
    o.textContent = `${d.name} (${d.teams.length})`;
    buildDivision.appendChild(o);
  });
  refreshTeamOptions();
}

/**
 * Re-fetch /api/divisions for the currently selected build season and repopulate
 * the division + team dropdowns. Called on boot and when #buildSeason changes.
 */
async function reloadBuildDivisions() {
  const season = el("buildSeason").value;
  try {
    const params = season ? `?season=${encodeURIComponent(season)}` : "";
    const res  = await fetch(`/api/divisions${params}`, { cache: "no-store" });
    const data = await res.json();
    populateDivisions(data);
  } catch (_e) { /* non-fatal — server may be starting */ }
}
el("buildSeason").addEventListener("change", reloadBuildDivisions);

/** Rebuild the team dropdown to match the currently selected division. */
function refreshTeamOptions() {
  const div = buildDivision.value;
  buildTeam.innerHTML = '<option value="">All teams</option>';
  const match = DIVISIONS.find((d) => d.name === div);
  if (!match) { buildTeam.disabled = true; return; }
  buildTeam.disabled = !SERVER_ONLINE;
  match.teams.forEach((t) => {
    const o = document.createElement("option");
    o.value = t; o.textContent = t;
    buildTeam.appendChild(o);
  });
}
buildDivision.addEventListener("change", refreshTeamOptions);

const consoleEl = el("console");
function logLine(text) {
  consoleEl.textContent += text + "\n";
  consoleEl.scrollTop = consoleEl.scrollHeight;   // auto-scroll to newest
}
el("clearLog").addEventListener("click", () => { consoleEl.textContent = ""; });

/**
 * Start a build. Opens an SSE stream to /api/run and pipes each log line into
 * the console. The button is disabled for the duration so a second build cannot
 * be started on top of the first (the server also guards this independently).
 */
el("buildBtn").addEventListener("click", () => {
  if (!SERVER_ONLINE || activeStream) return;
  const params = new URLSearchParams();
  const season = el("buildSeason").value;
  if (season)              params.set("season", season);
  if (buildDivision.value) params.set("division", buildDivision.value);
  if (buildTeam.value)     params.set("team", buildTeam.value);

  el("buildBtn").disabled = true;
  logLine("──────────────────────────────────────────");

  activeStream = new EventSource("/api/run?" + params.toString());
  activeStream.addEventListener("log",   (e) => logLine(JSON.parse(e.data)));
  activeStream.addEventListener("error", (e) => {
    // Custom server "error" events carry data; transport errors do not.
    if (e.data) logLine("⚠️  " + JSON.parse(e.data));
  });
  activeStream.addEventListener("done", (_e) => {
    activeStream.close();
    activeStream = null;
    el("buildBtn").disabled = false;
  });
  // If the connection itself drops without a "done", recover the button.
  activeStream.onerror = () => {
    if (activeStream && activeStream.readyState === EventSource.CLOSED) {
      activeStream = null;
      el("buildBtn").disabled = false;
    }
  };
});

// ── Reports tab ──────────────────────────────────────────────────────────────
let REPORTS = [];   // [{name, teams:[{name,hitting,pitching,mtime}]}, ...]

async function loadReports() {
  const list = el("reportsList");
  list.innerHTML = '<p class="empty">Loading…</p>';
  try {
    const season = el("reportsSeason").value;  // "" = all seasons
    const params = season ? `?season=${encodeURIComponent(season)}` : "";
    const res = await fetch(`/api/reports${params}`, { cache: "no-store" });
    const data = await res.json();
    REPORTS = data.divisions;
    renderReports();
  } catch (_e) {
    // View-only/offline: cannot list files without the server.
    list.innerHTML = '<p class="empty">Reports list needs the local server. '
      + "On mobile, open PDFs directly from the Google Drive app.</p>";
  }
}

function renderReports() {
  const filter = el("reportFilter").value.trim().toLowerCase();
  const list = el("reportsList");
  list.innerHTML = "";
  let shown = 0;

  REPORTS.forEach((div) => {
    const teams = div.teams.filter((t) => !filter || t.name.toLowerCase().includes(filter));
    if (!teams.length) return;
    shown += teams.length;

    const wrap = document.createElement("div");
    wrap.className = "report-div";
    wrap.innerHTML = `<h3>${div.name}</h3>`;

    teams.forEach((t) => {
      const row = document.createElement("div");
      row.className = "report-row";
      const hit = t.hitting
        ? `<a class="pill hit" href="/report/${encodeURI(t.hitting)}" target="_blank">Hitting</a>`
        : `<span class="pill hit off">Hitting</span>`;
      const pit = t.pitching
        ? `<a class="pill pit" href="/report/${encodeURI(t.pitching)}" target="_blank">Pitching</a>`
        : `<span class="pill pit off">Pitching</span>`;
      row.innerHTML = `<span class="name">${t.name}</span><span class="links">${hit}${pit}</span>`;
      wrap.appendChild(row);
    });
    list.appendChild(wrap);
  });

  if (!shown) list.innerHTML = '<p class="empty">No reports found.</p>';
}
el("refreshReports").addEventListener("click", loadReports);
el("reportFilter").addEventListener("input", renderReports);
el("reportsSeason").addEventListener("change", loadReports);

// ── Add-team tab ─────────────────────────────────────────────────────────────
el("addBtn").addEventListener("click", async () => {
  const out = el("addResult");
  out.className = "add-result";
  out.textContent = "Adding…";
  try {
    const res = await fetch("/api/add_team", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        season: el("addSeason").value,
        url: el("addUrl").value,
        division: el("addDivision").value,
        folder_name: el("addFolder").value,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      out.classList.add("ok");
      out.innerHTML = `✅ Added <strong>${data.folder_name}</strong> to ${data.division}.<br>`
        + `<span class="muted">${data.note}</span>`;
      el("addUrl").value = ""; el("addFolder").value = "";
      checkConnection().then((d) => { if (d) populateDivisions(d); });  // refresh team lists
    } else {
      out.classList.add("err");
      out.textContent = "❌ " + (data.error || "Could not add team.");
    }
  } catch (_e) {
    out.classList.add("err");
    out.textContent = "❌ Could not reach the server.";
  }
});

// ── Seasons tab ──────────────────────────────────────────────────────────────
/**
 * Load all seasons from /api/seasons and populate:
 *   1. The three per-tab season selects (Build, View Reports, Add Team)
 *   2. The seasons list in the Seasons tab
 *   3. The active-season label in the header
 */
async function loadSeasons() {
  try {
    const res  = await fetch("/api/seasons", { cache: "no-store" });
    const data = await res.json();
    populateTabSeasonSelects(data);
    renderSeasonsList(data);
    // Header sub-line shows active season name for quick reference
    const active = (data.seasons || []).find((s) => s.is_active);
    if (active) el("seasonLabel").textContent = "Season: " + active.display_name;
  } catch (_e) {
    // Non-fatal — server may just not be up yet during boot
  }
}

/**
 * Populate the three per-tab season <select> elements.
 *   buildSeason   — no "All" option (must target a specific season to build)
 *   reportsSeason — includes "All seasons" as first option
 *   addSeason     — no "All" option (must target a specific season to add a team)
 * Marks the currently active season as default selection on all three.
 */
function populateTabSeasonSelects(data) {
  const seasons = data.seasons || [];
  const activeId = data.active || "";

  // Build and Add Team selects: specific season only, active pre-selected
  ["buildSeason", "addSeason"].forEach((id) => {
    const sel = el(id);
    if (!sel) return;
    sel.innerHTML = "";
    seasons.forEach((s) => {
      const o = document.createElement("option");
      o.value    = s.id;
      o.textContent = s.display_name + (s.is_active ? " ✓" : "");
      o.selected = s.id === activeId;
      sel.appendChild(o);
    });
  });

  // Reports select: "All seasons" first, then each season; default to active
  const rSel = el("reportsSeason");
  if (!rSel) return;
  rSel.innerHTML = '<option value="">All seasons</option>';
  seasons.forEach((s) => {
    const o = document.createElement("option");
    o.value    = s.id;
    o.textContent = s.display_name + (s.is_active ? " ✓" : "");
    o.selected = s.id === activeId;   // default view to active season
    rSel.appendChild(o);
  });

  // After populating buildSeason, reload division/team lists for the new value
  reloadBuildDivisions();
}

/** Render the seasons list in the Seasons tab (name + active badge / Activate button). */
function renderSeasonsList(data) {
  const list = el("seasonsList");
  if (!list) return;
  list.innerHTML = "";

  if (!data.seasons || data.seasons.length === 0) {
    list.innerHTML = '<p class="empty">No seasons found.</p>';
    return;
  }

  data.seasons.forEach((s) => {
    const row = document.createElement("div");
    row.className = "season-row";

    if (s.is_active) {
      row.innerHTML =
        `<span class="season-name">${s.display_name}</span>` +
        `<span class="season-active-badge">● Active</span>`;
    } else {
      row.innerHTML =
        `<span class="season-name">${s.display_name}</span>` +
        `<button class="activate-btn" data-id="${s.id}">Activate</button>`;
    }
    list.appendChild(row);
  });

  // Wire Activate buttons
  list.querySelectorAll(".activate-btn").forEach((btn) => {
    btn.addEventListener("click", () => _activateSeason(btn.dataset.id));
  });
}

/**
 * Switch the active season by calling POST /api/seasons/active.
 * Shows a confirmation dialog first (this has pipeline-wide impact),
 * then displays a restart notice on success.
 */
async function _activateSeason(seasonId) {
  if (!confirm(
    `Switch active season to "${seasonId}"?\n\n` +
    "The server must be restarted for the change to take effect.\n" +
    "Any in-progress build will be unaffected."
  )) return;

  const out = el("seasonSwitchResult");
  out.className = "add-result";
  out.textContent = "Switching…";

  try {
    const res  = await fetch("/api/seasons/active", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ season_id: seasonId }),
    });
    const data = await res.json();

    if (data.ok) {
      out.className = "add-result ok";
      out.innerHTML =
        `✅ Active season updated to <strong>${seasonId}</strong>.<br>` +
        `<div class="restart-banner">` +
        `⚠️ <strong>Restart required:</strong> stop the server (Ctrl+C or close the terminal) ` +
        `and re-launch <code>Start Scout.command</code> for the change to take effect.` +
        `</div>`;
      // Refresh the seasons list to show new active state
      loadSeasons();
    } else {
      out.className = "add-result err";
      out.textContent = "❌ " + (data.error || "Could not switch season.");
    }
  } catch (_e) {
    out.className = "add-result err";
    out.textContent = "❌ Could not reach the server.";
  }
}

// Refresh seasons list button
el("refreshSeasons").addEventListener("click", loadSeasons);

// Auto-fill display name from season ID as the user types
el("newSeasonId").addEventListener("input", () => {
  const id = el("newSeasonId").value.trim();
  if (!id) return;
  const suggested = id.split("-")
    .map((p) => (p.match(/^\d+$/) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join(" ");
  // Only auto-fill if the user hasn't manually edited the display name
  if (!el("newSeasonDisplay").dataset.manualEdit) {
    el("newSeasonDisplay").value = suggested;
  }
});
el("newSeasonDisplay").addEventListener("input", () => {
  // Mark as manually edited so auto-fill stops overwriting it
  el("newSeasonDisplay").dataset.manualEdit = "1";
});

/**
 * Create a new season by calling POST /api/seasons.
 * Validates inputs, submits, shows next-step instructions on success.
 */
el("createSeasonBtn").addEventListener("click", async () => {
  const out = el("createSeasonResult");
  out.className = "add-result";

  const seasonId    = el("newSeasonId").value.trim();
  const displayName = el("newSeasonDisplay").value.trim();
  const majorsId    = el("newMajorsId").value.trim();
  const minorsId    = el("newMinorsId").value.trim();
  const setActive   = el("newSetActive").checked;

  if (!seasonId)  { out.className = "add-result err"; out.textContent = "❌ Season ID is required."; return; }
  if (!majorsId)  { out.className = "add-result err"; out.textContent = "❌ Majors GC org ID is required."; return; }
  if (!minorsId)  { out.className = "add-result err"; out.textContent = "❌ Minors GC org ID is required."; return; }

  out.textContent = "Creating…";
  try {
    const res  = await fetch("/api/seasons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        season_id:    seasonId,
        display_name: displayName || undefined,
        majors_gc_id: majorsId,
        minors_gc_id: minorsId,
        set_active:   setActive,
      }),
    });
    const data = await res.json();

    if (data.ok) {
      out.className = "add-result ok";
      let html = `✅ Season <strong>${seasonId}</strong> created.<br>` +
        `<span class="muted">Config: config/${data.yaml} &nbsp;|&nbsp; Data: seasons/${seasonId}/</span><br><br>` +
        `<strong>Next steps:</strong><br>` +
        `1. Add Majors + Minors teams to <code>config/${data.yaml}</code> after the draft.<br>` +
        `2. Wild/Storm opponents: use "Add Team" tab as games are scheduled.<br>` +
        `3. Run scrape_gc_boxscores.py after the first games to build rosters.`;
      if (data.restart_required) {
        html += `<div class="restart-banner">` +
          `⚠️ <strong>Restart required:</strong> stop the server and re-launch ` +
          `<code>Start Scout.command</code> to start using this season.` +
          `</div>`;
      }
      out.innerHTML = html;
      // Clear form + reset manual-edit flag
      ["newSeasonId", "newSeasonDisplay", "newMajorsId", "newMinorsId"].forEach((id) => {
        el(id).value = "";
        delete el(id).dataset.manualEdit;
      });
      el("newSetActive").checked = false;
      // Refresh seasons list to show the new entry
      loadSeasons();
    } else {
      out.className = "add-result err";
      out.textContent = "❌ " + (data.error || "Could not create season.");
    }
  } catch (_e) {
    out.className = "add-result err";
    out.textContent = "❌ Could not reach the server.";
  }
});

// ── Boot ─────────────────────────────────────────────────────────────────────
(async function boot() {
  const data = await checkConnection();
  if (data) {
    // loadSeasons → populateTabSeasonSelects → reloadBuildDivisions chains all
    // startup population: season selects, divisions, and teams in one flow.
    loadSeasons();
  } else {
    el("seasonLabel").textContent = "View-only mode";
  }
})();
