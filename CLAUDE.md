# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the web app
UV_CACHE_DIR=/tmp/uv-cache uv run python app.py

# Run the data analysis script directly
uv run python main.py

# Start JupyterLab
uv run jupyter lab
```

The web app is available at `http://127.0.0.1:8000`. `HOST` and `PORT` environment variables can override the defaults.

## Architecture

This project compares Wiesbaden city council (Stadtverordnetenwahl) election results between 2021 and 2026 across 26 districts (Ortsbezirke).

**Data layer** (`data/2021.csv`, `data/2026.csv`): Semicolon-separated CSVs with a `gebiet-name` column (district name) and columns `D1`–`D14/D15` for each party's vote count. Party numbering differs between years, so both files use numeric IDs that must be mapped.

**`main.py`**: Core data module. Loads both CSVs with Polars, renames numeric party columns to lowercase party names via `PARTY_MAP_OLD`/`PARTY_MAP_NEW`, joins the frames on `gebiet-name` (2026 columns get `_new` suffix on collision), and exposes:
- `df`: the joined `pl.DataFrame`, loaded at import time
- `parties`: set of 2026 party names (lowercase)
- `compare(party)`: returns per-district vote counts + `abs_change` / `rel_change` for a party
- `comparison_payload(party)`: JSON-serializable dict with summary stats and per-district rows for the web API

**`app.py`**: Single-file web server using Python's stdlib `ThreadingHTTPServer`. Imports `comparison_payload` and `parties` from `main.py`. Serves:
- `GET /` — the full SPA as inline HTML (CSS + vanilla JS in one string constant)
- `GET /api/parties` — sorted list of party names
- `GET /api/compare?party=<name>` — JSON payload for a given party

The frontend is entirely inline in `app.py`'s `HTML` string — no build step, no separate static files.

**`main.ipynb`**: Exploratory notebook that mirrors `main.py`'s logic; used for development and data exploration.

## Dependency management

Uses `uv` (see `pyproject.toml`). Key dependencies: `polars` (data processing), `jupyterlab` (notebook). No test framework is configured.
