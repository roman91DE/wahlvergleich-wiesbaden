from __future__ import annotations

import json
import pathlib

from app import HTML
from main import LEVELS, comparison_payload, parties

DOCS = pathlib.Path(__file__).resolve().parent / "docs"


def to_slug(party: str) -> str:
    return party.replace(" ", "-")


def build() -> None:
    DOCS.mkdir(exist_ok=True)
    data_dir = DOCS / "data"
    data_dir.mkdir(exist_ok=True)

    # parties.json
    (data_dir / "parties.json").write_text(
        json.dumps({"parties": sorted(parties)}, ensure_ascii=False),
        encoding="utf-8",
    )

    # one JSON per party × level
    for party in sorted(parties):
        for level in LEVELS:
            payload = comparison_payload(party, level)
            slug = to_slug(party)
            (data_dir / f"{slug}-{level}.json").write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"  {slug}-{level}.json")

    # Patch the two API fetch calls to use static paths instead
    html = HTML
    html = html.replace(
        'fetch("/api/parties")',
        'fetch("data/parties.json")',
    )
    html = html.replace(
        'const url = `/api/compare?party=${encodeURIComponent(state.party)}&level=${encodeURIComponent(state.level)}`;',
        'const url = `data/${state.party.replace(/ /g, "-")}-${state.level}.json`;',
    )
    (DOCS / "index.html").write_text(html, encoding="utf-8")

    n = len(parties) * len(LEVELS)
    print(f"Wrote {n} data files to docs/data/")
    print(f"Wrote docs/index.html ({len(html):,} bytes)")


if __name__ == "__main__":
    build()
