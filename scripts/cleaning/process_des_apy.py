"""
Process DES APY raw dataset.

Input:
    data/raw/des/des_apy_raw.csv

Output:
    data/processed/crop_yield/des_apy_2013_14_2022_23.csv

Purpose:
    - Filter DES APY data to 2013-14 through 2022-23
    - Select the initial project crop universe
    - Standardize column names
    - Standardize agricultural units
    - Calculate kg/ha and quintal/acre yield
    - Preserve source crop names and codes
    - Perform basic data-quality checks
"""

from pathlib import Path
import pandas as pd


#Path configuration

# Project root:
# agri-risk-roi-dashboard/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "des"
    / "des_apy_raw.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "crop_yield"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "des_apy_2013_14_2022_23.csv"
)


#Configuration
START_YEAR = "2013-2014"
END_YEAR = "2022-2023"

# Initial crop universe.
TARGET_CROPS = [
    "Rice",
    "Wheat",
    "Maize",
    "Jowar",
    "Bajra",
    "Ragi",
    "Soyabean",
    "Groundnut",
    "Gram",
    "Arhar/Tur",
    "Urad",
    "Sugarcane",
]


#Loading data
def load_data(path: Path) -> pd.DataFrame:
    """Loading the raw DES APY CSV."""

    if not path.exists():
        raise FileNotFoundError(
            f"Raw DES file not found:\n{path}\n\n"
            "Expected location:\n"
            "data/raw/des/des_apy_raw.csv"
        )

    print(f"Loading: {path}")

    df = pd.read_csv(path)

    print(f"Raw shape: {df.shape}")

    return df


#Basic validaion
def validate_raw_schema(df: pd.DataFrame) -> None:
    """Checking that required columns exist."""

    required_columns = [
        "year",
        "state_name",
        "state_code",
        "district_name",
        "district_code",
        "crop_name",
        "crop_code",
        "crop_type",
        "season",
        "area",
        "area_unit",
        "production",
        "production_unit",
        "yield",
        "yield_unit",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following required columns are missing:\n"
            + "\n".join(missing_columns)
        )

    print("Raw schema validation: PASSED")


#Filtering historical period
def filter_years(df: pd.DataFrame) -> pd.DataFrame:
    """Keeping only 2013-14 through 2022-23."""

    result = df[
        df["year"].between(
            START_YEAR,
            END_YEAR
        )
    ].copy()

    print(
        f"After year filtering: {result.shape}"
    )

    return result


#Filtering project crops
def filter_crops(df: pd.DataFrame) -> pd.DataFrame:
    """Keeping the initial project crop universe."""

    result = df[
        df["crop_name"].isin(TARGET_CROPS)
    ].copy()

    print(
        f"After crop filtering: {result.shape}"
    )

    missing_target_crops = sorted(
        set(TARGET_CROPS)
        - set(result["crop_name"].dropna().unique())
    )

    if missing_target_crops:
        print(
            "\nWARNING: The following target crops "
            "were not found:"
        )

        for crop in missing_target_crops:
            print(f"  - {crop}")

    return result


#Numeric conversion
def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Converting agricultural measurements to numeric values."""

    numeric_columns = [
        "area",
        "production",
        "yield",
    ]

    result = df.copy()

    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        )

    return result


#Unit standardization
def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creating a standardized agricultural measurement columns.

    Source:
        area       -> hectares
        production -> tonnes
        yield      -> tonnes/hectare

    Derived:
        yield_kg_ha
        yield_quintal_acre
    """

    result = df.copy()

    result["area_ha"] = result["area"]

    result["production_tonnes"] = (
        result["production"]
    )

    result["yield_tonnes_ha"] = (
        result["yield"]
    )

    # 1 tonne = 1000 kg
    result["yield_kg_ha"] = (
        result["yield_tonnes_ha"] * 1000
    )

    # 1 hectare = 2.47105 acres
    # 1 tonne = 10 quintals
    #
    # Therefore:
    #
    # quintals/acre = tonnes/hectare * 10 / 2.47105

    result["yield_quintal_acre"] = (
        result["yield_tonnes_ha"]
        * 10
        / 2.47105
    )

    return result


#creating standard crop column
def standardize_crop_columns(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Preserve original crop name and create a
    temporary standardized crop column.

    Formal cross-source crop mapping will be
    created later when MSP/UPAg data is available.
    """

    result = df.copy()

    result["crop"] = result["crop_name"]

    return result


#Selecting final columns
def select_final_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    result = df[
        [
            "state_name",
            "state_code",
            "district_name",
            "district_code",
            "crop",
            "crop_name",
            "crop_code",
            "crop_type",
            "season",
            "year",
            "area_ha",
            "production_tonnes",
            "yield_tonnes_ha",
            "yield_kg_ha",
            "yield_quintal_acre",
        ]
    ].copy()

    result = result.rename(
        columns={
            "state_name": "state",
            "district_name": "district",
            "crop_name": "crop_source_name",
        }
    )

    result["data_source"] = "DES_APY"

    return result


#Data quality checks
def run_quality_checks(df: pd.DataFrame) -> None:
    """Run basic quality checks."""

    print("\n" + "=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)

    # Shape
    print(f"\nRows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # Years
    print("\nYear coverage:")
    print(
        df["year"]
        .value_counts()
        .sort_index()
    )

    # Crops
    print("\nCrop coverage:")
    print(
        df["crop"]
        .value_counts()
    )

    # Missing values
    print("\nMissing values:")
    missing = (
        df.isna()
        .sum()
        .sort_values(ascending=False)
    )

    print(
        missing[missing > 0]
    )

    # Duplicate key
    key_columns = [
        "state",
        "district",
        "crop",
        "season",
        "year",
    ]

    duplicates = df.duplicated(
        subset=key_columns,
        keep=False
    )

    print(
        "\nDuplicate observations:",
        duplicates.sum()
    )

    # Negative values
    print(
        "\nNegative area:",
        (df["area_ha"] < 0).sum()
    )

    print(
        "Negative production:",
        (df["production_tonnes"] < 0).sum()
    )

    print(
        "Negative yield:",
        (df["yield_tonnes_ha"] < 0).sum()
    )

    # Zero values
    print(
        "\nZero production:",
        (df["production_tonnes"] == 0).sum()
    )

    print(
        "Zero yield:",
        (df["yield_tonnes_ha"] == 0).sum()
    )

    # Units
    print("\nSource area units:")
    print(df["area_ha"].dtype)

    print("\nData quality checks completed.")


#To save the output
def save_data(
    df: pd.DataFrame,
    output_path: Path
) -> None:
    """Save processed dataset."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nProcessed dataset saved to:\n"
        f"{output_path}"
    )


#Main pipeline
def main():

    print("=" * 60)
    print("DES APY PROCESSING PIPELINE")
    print("=" * 60)

    # Load
    df = load_data(RAW_PATH)

    # Validate
    validate_raw_schema(df)

    # Filter years
    df = filter_years(df)

    # Filter crops
    df = filter_crops(df)

    # Convert numeric values
    df = convert_numeric_columns(df)

    # Standardize units
    df = standardize_units(df)

    # Standardize crop columns
    df = standardize_crop_columns(df)

    # Select final columns
    df = select_final_columns(df)

    # Quality checks
    run_quality_checks(df)

    # Save
    save_data(df, OUTPUT_PATH)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()