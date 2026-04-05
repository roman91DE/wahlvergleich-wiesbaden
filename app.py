from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from main import LEVELS, comparison_payload, parties


HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))


HTML = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wiesbaden Wahlvergleich</title>
  <style>
    :root {
      --bg: #f6efe3;
      --bg-accent: #eadfce;
      --panel: rgba(253, 249, 242, 0.82);
      --panel-strong: rgba(255, 252, 247, 0.94);
      --ink: #1f1b18;
      --muted: #665d56;
      --line: rgba(44, 34, 25, 0.12);
      --warm: #b35c2e;
      --warm-soft: #eeb288;
      --cool: #0f5d73;
      --cool-soft: #8fd4e4;
      --shadow: 0 24px 70px rgba(78, 52, 32, 0.14);
      --radius-xl: 28px;
      --radius-lg: 22px;
      --radius-md: 16px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255, 255, 255, 0.72), transparent 35%),
        radial-gradient(circle at right 20%, rgba(143, 212, 228, 0.28), transparent 26%),
        linear-gradient(145deg, var(--bg) 0%, #f1e6d6 45%, var(--bg-accent) 100%);
      min-height: 100vh;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.32;
      background-image:
        linear-gradient(rgba(31, 27, 24, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 27, 24, 0.03) 1px, transparent 1px);
      background-size: 26px 26px;
      mask-image: radial-gradient(circle at center, black 25%, transparent 85%);
    }

    .page {
      width: min(1200px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 44px;
      position: relative;
      z-index: 1;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      margin-bottom: 18px;
    }

    .hero-card,
    .panel {
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(255, 255, 255, 0.5);
      box-shadow: var(--shadow);
      border-radius: var(--radius-xl);
    }

    .hero-card {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }

    .hero-card::after {
      content: "";
      position: absolute;
      right: -60px;
      top: -60px;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(238, 178, 136, 0.65), transparent 70%);
    }

    .eyebrow {
      margin: 0 0 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-size: 0.72rem;
      color: var(--warm);
      font-weight: 700;
    }

    h1 {
      margin: 0 0 12px;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-size: clamp(2.2rem, 4vw, 4rem);
      line-height: 0.95;
      max-width: 10ch;
    }

    .hero-copy {
      margin: 0;
      max-width: 56ch;
      color: var(--muted);
      line-height: 1.6;
      font-size: 1.02rem;
    }

    .controls {
      padding: 24px;
      display: grid;
      gap: 14px;
      align-content: start;
    }

    .control-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    label {
      display: grid;
      gap: 8px;
      font-size: 0.88rem;
      color: var(--muted);
      font-weight: 700;
    }

    select,
    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      font: inherit;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.78);
      outline: none;
    }

    select:focus,
    input:focus {
      border-color: rgba(15, 93, 115, 0.4);
      box-shadow: 0 0 0 4px rgba(143, 212, 228, 0.22);
    }

    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }

    .chip {
      border: none;
      border-radius: 999px;
      padding: 10px 14px;
      background: rgba(255, 255, 255, 0.84);
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 700;
      transition: transform 160ms ease, background 160ms ease, color 160ms ease;
    }

    .chip.active {
      background: linear-gradient(135deg, var(--cool), #1b819c);
      color: white;
      transform: translateY(-1px);
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 18px;
    }

    .stat {
      padding: 20px;
      background: var(--panel-strong);
      border-radius: var(--radius-lg);
      border: 1px solid rgba(255, 255, 255, 0.72);
      box-shadow: var(--shadow);
      transform: translateY(12px);
      opacity: 0;
      animation: rise 500ms ease forwards;
    }

    .stat:nth-child(2) { animation-delay: 70ms; }
    .stat:nth-child(3) { animation-delay: 140ms; }
    .stat:nth-child(4) { animation-delay: 210ms; }

    .stat-label {
      margin: 0 0 14px;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }

    .stat-value {
      margin: 0 0 8px;
      font-size: clamp(1.7rem, 3vw, 2.8rem);
      font-weight: 800;
      line-height: 1;
    }

    .stat-note {
      margin: 0;
      color: var(--muted);
      font-size: 0.95rem;
    }

    .layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }

    .panel {
      padding: 22px;
    }

    .panel-header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
    }

    .panel-title {
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
      font-size: 1.55rem;
    }

    .panel-copy {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 0.96rem;
    }

    .bar-list {
      display: grid;
      gap: 14px;
    }

    .bar-row {
      display: grid;
      gap: 8px;
    }

    .bar-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 0.95rem;
    }

    .bar-meta strong {
      font-weight: 800;
    }

    .track {
      position: relative;
      height: 14px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(15, 93, 115, 0.08);
    }

    .bar {
      position: absolute;
      inset: 0 auto 0 0;
      width: 0;
      border-radius: inherit;
      transition: width 320ms ease;
    }

    .bar.warm {
      background: linear-gradient(90deg, var(--warm), var(--warm-soft));
    }

    .bar.cool {
      background: linear-gradient(90deg, var(--cool), var(--cool-soft));
    }

    .table-wrap {
      margin-top: 18px;
      overflow: auto;
      border-radius: 20px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 720px;
    }

    thead th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(246, 239, 227, 0.95);
      color: var(--muted);
      text-align: left;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }

    th, td {
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }

    tbody tr:hover {
      background: rgba(255, 255, 255, 0.64);
    }

    .delta {
      font-weight: 800;
    }

    .delta.pos { color: var(--cool); }
    .delta.neg { color: #9f2d19; }

    .subtle {
      color: var(--muted);
    }

    .loading {
      color: var(--muted);
      font-size: 0.96rem;
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .source-note {
      margin-top: 28px;
      text-align: center;
      font-size: 0.82rem;
      color: var(--muted);
    }

    .source-note a {
      color: var(--cool);
      text-decoration: none;
    }

    .source-note a:hover {
      text-decoration: underline;
    }

    @media (max-width: 980px) {
      .hero,
      .layout {
        grid-template-columns: 1fr;
      }

      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 640px) {
      .page {
        width: min(100%, calc(100% - 20px));
        padding-top: 18px;
      }

      .hero-card,
      .panel,
      .controls {
        padding: 18px;
      }

      .control-grid,
      .stats {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <article class="hero-card">
        <p class="eyebrow">Stadtverordnetenwahl Wiesbaden</p>
        <h1>Wahlvergleich Wiesbaden</h1>
        <p class="hero-copy">
          Vergleiche die Ergebnisse der Wiesbadener Stadtverordnetenwahl 2021 und 2026
          auf Ebene der Ortsbezirke oder Wahlbezirke. Wechsle zwischen Parteien, sortiere
          nach absoluten oder relativen Verschiebungen und filtere gezielt nach Gebieten.
        </p>
      </article>

      <aside class="hero-card controls">
        <div>
          <p class="eyebrow">Steuerung</p>
          <div class="control-grid">
            <label>
              Partei
              <select id="partySelect"></select>
            </label>
            <label>
              Ortsbezirk suchen
              <input id="searchInput" type="search" placeholder="Ortsbezirk suchen">
            </label>
          </div>
        </div>

        <div>
          <label>Gebietsebene</label>
          <div id="levelChips" class="chips">
            <button class="chip active" data-level="Ortsbezirk">Ortsbezirke</button>
            <button class="chip" data-level="Wahlbezirk">Wahlbezirke</button>
          </div>
        </div>

        <div>
          <label>Sortierung</label>
          <div id="sortChips" class="chips">
            <button class="chip active" data-sort="abs_change">Absolute Veränderung</button>
            <button class="chip" data-sort="rel_change">Relative Veränderung</button>
            <button class="chip" data-sort="votes_2026">Stimmen 2026</button>
            <button class="chip" data-sort="gebiet-name">Gebiet</button>
          </div>
        </div>
      </aside>
    </section>

    <section id="stats" class="stats"></section>

    <section class="layout">
      <article class="panel">
        <div class="panel-header">
          <div>
            <h2 class="panel-title">Größte Bewegungen</h2>
            <p class="panel-copy">Die auffälligsten Gebiete nach aktueller Sortierung.</p>
          </div>
          <span id="listCount" class="subtle"></span>
        </div>
        <div id="barList" class="bar-list">
          <p class="loading">Diagramm wird geladen…</p>
        </div>
      </article>

      <article class="panel">
        <div class="panel-header">
          <div>
            <h2 class="panel-title">Ergebnisse nach Ortsbezirk</h2>
            <p class="panel-copy">Stimmen 2021, Stimmen 2026 und Veränderungen je Gebiet.</p>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th id="tableGebietHeader">Ortsbezirk</th>
                <th>2021</th>
                <th>2026</th>
                <th>Absolut</th>
                <th>Relativ</th>
              </tr>
            </thead>
            <tbody id="tableBody">
              <tr><td colspan="5" class="loading">Zeilen werden geladen…</td></tr>
            </tbody>
          </table>
        </div>
      </article>
    </section>
    <p class="source-note">Datenquelle: <a href="https://votemanager-wi.ekom21cdn.de/2026-03-15/06414000/praesentation/opendata.html" target="_blank" rel="noopener">Open Data – Stadtverordnetenwahl Wiesbaden 2021 &amp; 2026</a></p>
  </main>

  <script>
    const state = {
      party: null,
      sortKey: "abs_change",
      search: "",
      payload: null,
      parties: [],
      level: "Ortsbezirk",
    };

    const number = new Intl.NumberFormat("de-DE");
    const percent = new Intl.NumberFormat("de-DE", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });

    const partySelect = document.querySelector("#partySelect");
    const searchInput = document.querySelector("#searchInput");
    const sortChips = [...document.querySelectorAll("#sortChips .chip")];
    const levelChips = [...document.querySelectorAll("#levelChips .chip")];
    const stats = document.querySelector("#stats");
    const barList = document.querySelector("#barList");
    const tableBody = document.querySelector("#tableBody");
    const tableGebietHeader = document.querySelector("#tableGebietHeader");
    const listCount = document.querySelector("#listCount");

    function formatSignedInt(value) {
      const prefix = value > 0 ? "+" : "";
      return `${prefix}${number.format(value)}`;
    }

    function formatSignedPercent(value) {
      if (value == null || Number.isNaN(value)) return "neu";
      const prefix = value > 0 ? "+" : "";
      return `${prefix}${percent.format(value)}%`;
    }

    function deltaClass(value) {
      if (value > 0) return "pos";
      if (value < 0) return "neg";
      return "";
    }

    function sortRows(rows) {
      const sorted = [...rows];
      sorted.sort((a, b) => {
        if (state.sortKey === "gebiet-name") {
          return a["gebiet-name"].localeCompare(b["gebiet-name"]);
        }

        const aValue = a[state.sortKey] ?? Number.NEGATIVE_INFINITY;
        const bValue = b[state.sortKey] ?? Number.NEGATIVE_INFINITY;
        return bValue - aValue;
      });
      return sorted;
    }

    function filteredRows() {
      const rows = state.payload?.rows ?? [];
      const needle = state.search.trim().toLowerCase();
      const filtered = needle
        ? rows.filter((row) => row["gebiet-name"].toLowerCase().includes(needle))
        : rows;
      return sortRows(filtered);
    }

    function renderStats(summary) {
      const cards = [
        {
          label: "Gesamtstimmen 2026",
          value: number.format(summary.total_votes_2026),
          note: `${formatSignedInt(summary.abs_change)} gegenüber 2021`,
        },
        {
          label: "Relative Veränderung",
          value: formatSignedPercent(summary.rel_change),
          note: summary.rel_change == null
            ? "Neue Partei ohne Vergleichsbasis aus 2021"
            : `Über ${summary.districts} Ortsbezirke hinweg`,
        },
        {
          label: "Größter absoluter Zugewinn",
          value: summary.top_gainer,
          note: "Hier stieg die Stimmenzahl am stärksten",
        },
        {
          label: "Stärkster relativer Zugewinn",
          value: summary.strongest_relative_gain,
          note: summary.rel_change == null
            ? `${state.party.toUpperCase()} tritt 2026 neu an`
            : `Hier legte ${state.party.toUpperCase()} prozentual am stärksten zu`,
        },
      ];

      stats.innerHTML = cards.map((card) => `
        <article class="stat">
          <p class="stat-label">${card.label}</p>
          <p class="stat-value">${card.value}</p>
          <p class="stat-note">${card.note}</p>
        </article>
      `).join("");
    }

    function renderBars(rows) {
      const mode = state.sortKey === "gebiet-name" ? "abs_change" : state.sortKey;
      const topRows = rows.slice(0, 8);
      const maxMagnitude = Math.max(
        1,
        ...topRows.map((row) => Math.abs(row[mode] ?? 0)),
      );

      listCount.textContent = `${rows.length} Ortsbezirk${rows.length === 1 ? "" : "e"}`;

      if (!topRows.length) {
        barList.innerHTML = `<p class="loading">Kein Ortsbezirk passt zum aktuellen Filter.</p>`;
        return;
      }

      barList.innerHTML = topRows.map((row) => {
        const raw = row[mode] ?? 0;
        const width = Math.max(6, Math.abs(raw) / maxMagnitude * 100);
        const isPercent = mode === "rel_change";
        const label = isPercent ? formatSignedPercent(raw) : formatSignedInt(raw);
        const color = raw >= 0 ? "cool" : "warm";
        return `
          <div class="bar-row">
            <div class="bar-meta">
              <span><strong>${row["gebiet-name"]}</strong></span>
              <span class="delta ${deltaClass(raw)}">${label}</span>
            </div>
            <div class="track">
              <div class="bar ${color}" style="width: ${width}%"></div>
            </div>
          </div>
        `;
      }).join("");
    }

    function renderTable(rows) {
      if (!rows.length) {
        tableBody.innerHTML = `<tr><td colspan="5" class="loading">Kein Ortsbezirk passt zum aktuellen Filter.</td></tr>`;
        return;
      }

      tableBody.innerHTML = rows.map((row) => `
        <tr>
          <td><strong>${row["gebiet-name"]}</strong></td>
          <td>${number.format(row.votes_2021)}</td>
          <td>${number.format(row.votes_2026)}</td>
          <td class="delta ${deltaClass(row.abs_change)}">${formatSignedInt(row.abs_change)}</td>
          <td class="delta ${deltaClass(row.rel_change ?? 0)}">${formatSignedPercent(row.rel_change)}</td>
        </tr>
      `).join("");
    }

    async function loadParties() {
      const response = await fetch("/api/parties");
      const data = await response.json();
      state.parties = data.parties;
      partySelect.innerHTML = state.parties.map((party) => `
        <option value="${party}">${party.toUpperCase()}</option>
      `).join("");
      state.party = state.parties[0];
      partySelect.value = state.party;
    }

    async function loadPartyData() {
      const url = `/api/compare?party=${encodeURIComponent(state.party)}&level=${encodeURIComponent(state.level)}`;
      const response = await fetch(url);
      state.payload = await response.json();
      const gebietLabel = state.level === "Wahlbezirk" ? "Wahlbezirk" : "Ortsbezirk";
      tableGebietHeader.textContent = gebietLabel;
      searchInput.placeholder = `${gebietLabel} suchen`;
      const rows = filteredRows();
      renderStats(state.payload.summary);
      renderBars(rows);
      renderTable(rows);
    }

    partySelect.addEventListener("change", async (event) => {
      state.party = event.target.value;
      await loadPartyData();
    });

    searchInput.addEventListener("input", () => {
      state.search = searchInput.value;
      const rows = filteredRows();
      renderBars(rows);
      renderTable(rows);
    });

    sortChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        state.sortKey = chip.dataset.sort;
        sortChips.forEach((button) => button.classList.toggle("active", button === chip));
        const rows = filteredRows();
        renderBars(rows);
        renderTable(rows);
      });
    });

    levelChips.forEach((chip) => {
      chip.addEventListener("click", async () => {
        state.level = chip.dataset.level;
        state.search = "";
        searchInput.value = "";
        levelChips.forEach((button) => button.classList.toggle("active", button === chip));
        await loadPartyData();
      });
    });

    async function boot() {
      await loadParties();
      await loadPartyData();
    }

    boot().catch((error) => {
      console.error(error);
      stats.innerHTML = "";
      barList.innerHTML = `<p class="loading">Beim Laden der Daten ist ein Fehler aufgetreten.</p>`;
      tableBody.innerHTML = `<tr><td colspan="5" class="loading">Mehr Details findest du in der Browser-Konsole.</td></tr>`;
    });
  </script>
</body>
</html>
"""


class ElectionAppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.respond_html(HTML)
            return

        if parsed.path == "/api/parties":
            self.respond_json({"parties": sorted(parties)})
            return

        if parsed.path == "/api/compare":
            query = parse_qs(parsed.query)
            party = query.get("party", [""])[0].strip().lower()
            if not party:
                self.respond_json({"error": "Der Query-Parameter 'party' ist erforderlich."}, status=HTTPStatus.BAD_REQUEST)
                return

            level_raw = query.get("level", ["Ortsbezirk"])[0].strip()
            level = level_raw if level_raw in LEVELS else "Ortsbezirk"

            try:
                payload = comparison_payload(party, level)
            except ValueError as exc:
                self.respond_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return

            self.respond_json(payload)
            return

        self.respond_json({"error": "Nicht gefunden"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def respond_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = html.encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def respond_json(
        self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ElectionAppHandler)
    print(f"Wahlvergleich Wiesbaden läuft auf http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
