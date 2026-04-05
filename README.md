# Wahlvergleich Wiesbaden

Dieses Repo enthält jetzt eine kleine lokale Web-App, mit der sich die Ergebnisse der Wiesbadener Stadtverordnetenwahl 2021 und 2026 interaktiv vergleichen lassen.

## Starten

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python app.py
```

Anschließend `http://127.0.0.1:8000` im Browser öffnen.

## Funktionen

- Nutzt die Vergleichslogik aus [main.py](/Users/roman/repos/test_reports/main.py)
- Erlaubt den interaktiven Wechsel zwischen Parteien
- Zeigt absolute und relative Veränderungen je Ortsbezirk
- Enthält Kennzahlen, eine Rangliste der stärksten Verschiebungen und eine durchsuchbare Ergebnistabelle
