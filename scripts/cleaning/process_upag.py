from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "upag"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "crop_yield"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


CROP_CONFIG = {
    "Rice": "rice",
    "Wheat": "wheat",
    "Maize": "maz",
    "Urad": "urad",
}


def process_crop(crop_name, prefix):

    input_path = (
        RAW_DIR
        / f"{crop_name.lower()}_upag_raw.csv"
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"File not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    records = []

    for year_suffix, year_label in [
        ("23", "2022-2023"),
        ("24", "2023-2024"),
        ("25", "2024-2025"),
    ]:

        area_col = f"{prefix}area{year_suffix}"
        prod_col = f"{prefix}prod{year_suffix}"
        yield_col = f"{prefix}yld{year_suffix}"

        temp = df[
            [
                "district",
                "state",
                "lgd_distcode",
                "lgd_statecode",
                "cencode2011",
                area_col,
                prod_col,
                yield_col,
            ]
        ].copy()

        temp["year"] = year_label
        temp["crop"] = crop_name

        temp = temp.rename(
            columns={
                "district": "district",
                "state": "state",
                "lgd_distcode": "district_code",
                "lgd_statecode": "state_code",
                "cencode2011": "census_code",
                area_col: "area_lakh_ha",
                prod_col: "production_lakh_tonnes",
                yield_col: "yield_kg_ha",
            }
        )

        # UPAg area is reported in lakh hectares
        temp["area_ha"] = (
            temp["area_lakh_ha"] * 100000
        )

        # UPAg production is reported in lakh tonnes
        temp["production_tonnes"] = (
            temp["production_lakh_tonnes"]
            * 100000
        )

        # Convert kg/ha → tonnes/ha
        temp["yield_tonnes_ha"] = (
            temp["yield_kg_ha"] / 1000
        )

        # Convert kg/ha → quintal/acre
        temp["yield_quintal_acre"] = (
            temp["yield_kg_ha"]
            / 100
            / 2.47105
        )

        temp["crop_source_name"] = crop_name
        temp["data_source"] = "UPAg"

        records.append(temp)

    result = pd.concat(
        records,
        ignore_index=True
    )

    return result


def main():

    all_crops = []

    for crop, prefix in CROP_CONFIG.items():

        print(
            f"Processing {crop}..."
        )

        crop_df = process_crop(
            crop,
            prefix
        )

        all_crops.append(crop_df)

    final_df = pd.concat(
        all_crops,
        ignore_index=True
    )

    final_columns = [
        "state",
        "state_code",
        "district",
        "district_code",
        "census_code",
        "crop",
        "crop_source_name",
        "year",
        "area_lakh_ha",
        "area_ha",
        "production_lakh_tonnes",
        "production_tonnes",
        "yield_kg_ha",
        "yield_tonnes_ha",
        "yield_quintal_acre",
        "data_source",
    ]

    final_df = final_df[
        final_columns
    ]

    output_path = (
        OUTPUT_DIR
        / "upag_2022_23_2024_25.csv"
    )

    final_df.to_csv(
        output_path,
        index=False
    )

    print("\nCompleted.")
    print(
        "Shape:",
        final_df.shape
    )

    print(
        "Saved:",
        output_path
    )


if __name__ == "__main__":
    main()