# Wahlvergleich Wiesbaden

Interaktiver Vergleich der Wiesbadener Stadtverordnetenwahl 2021 und 2026 nach Ortsbezirken.

**Statische Demo:** [roman91de.github.io/wahlvergleich-wiesbaden](https://roman91de.github.io/wahlvergleich-wiesbaden/)

## Funktionen

- Vergleich aller Parteien zwischen den Wahljahren 2021 und 2026
- Absolute und relative Veränderungen je Ortsbezirk
- Zusammenfassende Kennzahlen und Rangliste der stärksten Verschiebungen
- Durchsuchbare Ergebnistabelle

## Lokale Web-App starten

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python app.py
```

Anschließend `http://127.0.0.1:8000` im Browser öffnen. `HOST` und `PORT` können über Umgebungsvariablen angepasst werden.

## Aufbau

| Datei/Ordner | Beschreibung |
|---|---|
| `data/2021.csv`, `data/2026.csv` | Rohdaten der Wahlergebnisse je Ortsbezirk |
| `main.py` | Datenverarbeitung mit Polars, Vergleichslogik |
| `app.py` | Lokaler Webserver (stdlib `ThreadingHTTPServer`), SPA als Inline-HTML |
| `docs/` | Statisch generierte Site für GitHub Pages |
| `main.ipynb` | Exploratives Notebook |

## Abhängigkeiten

Abhängigkeiten werden über `uv` verwaltet (siehe `pyproject.toml`). Hauptabhängigkeiten: `polars`, `jupyterlab`.

```bash
# Notebook starten
uv run jupyter lab
```
