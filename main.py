from __future__ import annotations

import pathlib

import polars as pl


DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"

PARTY_MAP_2026 = {
    1: "CDU",
    2: "AfD",
    3: "SPD",
    4: "GRÜNE",
    5: "FDP",
    6: "DIE LINKE",
    7: "Volt",
    8: "PRO AUTO",
    9: "BLW",
    10: "Die PARTEI",
    11: "Die Gerechtigkeitspartei",
    12: "BSW",
    13: "FWG",
    14: "PdF",
    15: "FREIE WÄHLER",
}

PARTY_MAP_2021 = {
    1: "CDU",
    2: "GRÜNE",
    3: "SPD",
    4: "AfD",
    5: "FDP",
    6: "Die Linke",
    7: "BLW",
    8: "FREIE WÄHLER",
    9: "ULW",
    10: "LKR",
    11: "Die PARTEI",
    12: "Volt",
    13: "BIG",
    14: "Pro Auto",
}

LEVELS = ("Ortsbezirk", "Wahlbezirk")


def normalize(d: dict[int, str]) -> dict[str, str]:
    return {f"D{k}": v.lower() for k, v in d.items()}


def read_file(path: pathlib.Path) -> pl.LazyFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing election data file: {path}")
    return pl.scan_csv(source=path, separator=";").select(
        pl.col("gebiet-nr", "gebiet-name", r"^D\d+$")
    )


def build_joined_frame(level: str) -> pl.DataFrame:
    file_2021 = DATA_DIR / f"2021_Open-Data-06414000-Stadtverordnetenwahl-{level}.csv"
    file_2026 = DATA_DIR / f"2026_Open-Data-06414000-Stadtverordnetenwahl-{level}.csv"
    old_frame = read_file(file_2021).rename(mapping=normalize(PARTY_MAP_2021))
    new_frame = read_file(file_2026).rename(mapping=normalize(PARTY_MAP_2026))

    if level == "Wahlbezirk":
        # Full outer join on precinct number so unmatched precincts from either
        # year are retained (zero-filled) rather than silently dropped.
        # Polars coalesces the join key automatically in how="full".
        joined = old_frame.join(new_frame, on="gebiet-nr", how="full", suffix="_new")
        joined = joined.with_columns(
            pl.coalesce(pl.col("gebiet-name_new"), pl.col("gebiet-name")).alias(
                "gebiet-name"
            )
        ).drop("gebiet-name_new")
        return joined.collect()

    joined = old_frame.join(new_frame, on="gebiet-name", how="left", suffix="_new")
    return joined.collect()


_frames: dict[str, pl.DataFrame] = {
    level: build_joined_frame(level) for level in LEVELS
}

old_parties = set(normalize(PARTY_MAP_2021).values())
new_parties = set(normalize(PARTY_MAP_2026).values())
parties = old_parties | new_parties


def votes_2021_expr(party: str, df: pl.DataFrame) -> pl.Expr:
    if party in df.columns and party in old_parties:
        return pl.col(party).fill_null(0)
    return pl.lit(0)


def votes_2026_expr(party: str, df: pl.DataFrame) -> pl.Expr:
    new_column = f"{party}_new"
    if new_column in df.columns:
        return pl.col(new_column).fill_null(0)
    if party in df.columns and party in new_parties:
        return pl.col(party).fill_null(0)
    return pl.lit(0)


def compare(party: str, level: str = "Ortsbezirk") -> pl.DataFrame:
    normalized_party = party.lower()
    if normalized_party not in parties:
        available = ", ".join(sorted(parties))
        raise ValueError(
            f"Unbekannte Partei '{party}'. Verfügbare Parteien: {available}"
        )
    if level not in LEVELS:
        raise ValueError(
            f"Unbekannte Gebietsebene '{level}'. Verfügbar: {', '.join(LEVELS)}"
        )
    df = _frames[level]
    return (
        df.select(
            "gebiet-name",
            votes_2021_expr(normalized_party, df).alias("votes_2021"),
            votes_2026_expr(normalized_party, df).alias("votes_2026"),
        )
        .with_columns(
            abs_change=pl.col("votes_2026") - pl.col("votes_2021"),
            rel_change=pl.when(pl.col("votes_2021") == 0)
            .then(None)
            .otherwise(
                (pl.col("votes_2026") - pl.col("votes_2021"))
                / pl.col("votes_2021")
                * 100
            ),
        )
        .sort("abs_change", descending=True)
    )


def comparison_payload(party: str, level: str = "Ortsbezirk") -> dict[str, object]:
    frame = compare(party, level)
    records = frame.to_dicts()

    total_2021 = int(frame["votes_2021"].sum())
    total_2026 = int(frame["votes_2026"].sum())
    abs_change = total_2026 - total_2021
    rel_change = None if total_2021 == 0 else abs_change / total_2021 * 100

    top_gainer = max(records, key=lambda row: row["abs_change"])
    top_loser = min(records, key=lambda row: row["abs_change"])
    strongest_relative = max(
        records,
        key=lambda row: float("-inf")
        if row["rel_change"] is None
        else row["rel_change"],
    )

    return {
        "party": party.lower(),
        "level": level,  # always a valid LEVELS value — compare() raises otherwise
        "summary": {
            "districts": len(records),
            "total_votes_2021": total_2021,
            "total_votes_2026": total_2026,
            "abs_change": abs_change,
            "rel_change": rel_change,
            "top_gainer": top_gainer["gebiet-name"],
            "top_loser": top_loser["gebiet-name"],
            "strongest_relative_gain": strongest_relative["gebiet-name"],
        },
        "rows": records,
    }


if __name__ == "__main__":
    print("Verfügbare Parteien:")
    for party_name in sorted(parties):
        print(f"- {party_name}")
