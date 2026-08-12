"""
Processing the Government DES district-level Area, Production & Yield report.

Input: raw_data/crop/horizontal_crop_vertical_year_report.xls
Output:data/cleaned_crop_data.csv

The DES file has an .xls extension but is an HTML table with 3-level headers, so pandas.read_html() is used instead of read_excel().
"""

from pathlib import Path
import re
import pandas as pd
import numpy as np


INPUT_FILE = Path("raw_data/crop/horizontal_crop_vertical_year_report.xls")
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "cleaned_crop_data.csv"

METRICS = [
    "Area (Hectare)",
    "Production (Tonnes)",
    "Yield (Tonne/Hectare)",
]


def clean_location_name(value: object) -> str:
    """Remove the numeric prefix used by the DES report."""
    value = str(value).strip()
    return re.sub(r"^\d+\.\s*", "", value)


def load_des_report(path: Path) -> pd.DataFrame:
    """Read the DES HTML report disguised as an .xls file."""
    tables = pd.read_html(path)

    if not tables:
        raise ValueError("No table was found in the DES report.")

    df = tables[0]

    if df.shape[1] < 4 or df.columns.nlevels != 3:
        raise ValueError(
            f"Unexpected DES format: shape={df.shape}, "
            f"column_levels={df.columns.nlevels}"
        )

    return df


def transform_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Crop/Season/Metric columns into one row per observation."""

    identifiers = pd.DataFrame(
        {
            "state": df.iloc[:, 0].map(clean_location_name),
            "district": df.iloc[:, 1].map(clean_location_name),
            "year": df.iloc[:, 2].astype(str).str.strip(),
        }
    )

    # Every crop-season combination occupies a group of metric columns.
    crop_seasons = sorted(
        set((column[0], column[1]) for column in df.columns[3:])
    )

    records = []

    for crop, season in crop_seasons:
        available = [
            metric
            for metric in METRICS
            if (crop, season, metric) in df.columns
        ]

        block = df.loc[:, [(crop, season, metric) for metric in available]].copy()
        block.columns = available

        # Convert DES numeric cells safely.
        for metric in available:
            block[metric] = pd.to_numeric(block[metric], errors="coerce")

        # Ignore completely empty crop-season observations.
        mask = block.notna().any(axis=1)

        if not mask.any():
            continue

        result = identifiers.loc[mask].copy()
        result["crop"] = crop
        result["season"] = season

        result["area_hectare"] = (
            block.loc[mask, "Area (Hectare)"]
            if "Area (Hectare)" in block
            else np.nan
        )
        result["production_tonnes"] = (
            block.loc[mask, "Production (Tonnes)"]
            if "Production (Tonnes)" in block
            else np.nan
        )
        result["yield_tonne_per_hectare"] = (
            block.loc[mask, "Yield (Tonne/Hectare)"]
            if "Yield (Tonne/Hectare)" in block
            else np.nan
        )

        records.append(result)

    if not records:
        raise ValueError("No crop observations were found.")

    result = pd.concat(records, ignore_index=True)

    # Extract the starting year as an integer for time-series operations.
    result["year_start"] = pd.to_numeric(
        result["year"].str.extract(r"(\d{4})")[0],
        errors="coerce",
    ).astype("Int64")

    # Independent calculation used for validation later.
    result["yield_calculated"] = np.where(
        result["area_hectare"] > 0,
        result["production_tonnes"] / result["area_hectare"],
        np.nan,
    )

    return result


def validate(result: pd.DataFrame) -> None:
    """Run basic data-quality checks and print a summary."""

    key = ["state", "district", "year", "crop", "season"]

    duplicates = result.duplicated(key).sum()
    negative_area = (result["area_hectare"] < 0).sum()
    negative_production = (result["production_tonnes"] < 0).sum()

    print("\n--- DATA QUALITY SUMMARY ---")
    print(f"Rows: {len(result):,}")
    print(f"Columns: {len(result.columns)}")
    print(f"States: {result['state'].nunique():,}")
    print(f"Districts: {result['district'].nunique():,}")
    print(f"Crops: {result['crop'].nunique():,}")
    print(f"Seasons: {result['season'].nunique():,}")
    print(f"Years: {result['year'].nunique():,}")
    print(f"Duplicate keys: {duplicates:,}")
    print(f"Negative area values: {negative_area:,}")
    print(f"Negative production values: {negative_production:,}")

    print("\nMissing values:")
    print(result.isna().sum())

    if duplicates:
        print("\nWARNING: Duplicate observation keys were found.")

    if negative_area or negative_production:
        print("\nWARNING: Negative agricultural measurements were found.")


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Place the downloaded DES file in raw_data/crop/."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Reading Government DES report...")
    raw = load_des_report(INPUT_FILE)

    print(f"Raw shape: {raw.shape}")

    cleaned = transform_to_long(raw)

    # Keep a deterministic column order.
    columns = [
        "state",
        "district",
        "year",
        "year_start",
        "crop",
        "season",
        "area_hectare",
        "production_tonnes",
        "yield_tonne_per_hectare",
        "yield_calculated",
    ]
    cleaned = cleaned[columns]

    validate(cleaned)

    cleaned.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Output size: {OUTPUT_FILE.stat().st_size / (1024**2):.2f} MB")


if __name__ == "__main__":
    main()