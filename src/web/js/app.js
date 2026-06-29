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
  // Disable build/add controls when the engine is unreachable.
  ["buildBtn", "addBtn", "buildDivision", "buildTeam", "addUrl", "addDivision", "addFolder"]
    .forEach((id) => { const n = el(id); if (n) n.disabled = !online; });
}

// ── Build tab ────────────────────────────────────────────────────────────────
const buildDivision = el("buildDivision");
const buildTeam     = el("buildTeam");
let DIVISIONS = [];   // [{name, type, teams:[...]}, ...]

/** Populate the division dropdown and wire the team dropdown to follow it. */
function populateDivisions(data) {
  el("seasonLabel").textContent = "Season: " + data.season;
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
    const res = await fetch("/api/reports", { cache: "no-store" });
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

// ── Boot ─────────────────────────────────────────────────────────────────────
(async function boot() {
  const data = await checkConnection();
  if (data) populateDivisions(data);
  else el("seasonLabel").textContent = "View-only mode";
})();
