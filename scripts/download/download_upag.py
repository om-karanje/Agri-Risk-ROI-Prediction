"""
To Download recent UPAg district-level APY data.
Years:2022-23, 2023-24, 2024-25
Source: Unified Portal for Agricultural Statistics (UPAg) Department of Agriculture & Farmers Welfare

The current implementation uses the government-linked Esri India REST layers that expose UPAg APY data.
"""

from pathlib import Path
import requests
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "upag"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# UPAg / Esri REST layers
CROP_LAYERS = {

    "Rice": (
        "https://livingatlas.esri.in/server/rest/services/"
        "AgricultureCensus/"
        "India_Agriculture_Statistics_2022_2023_Rice_Production/"
        "MapServer/0"
    ),

    "Wheat": (
        "https://livingatlas.esri.in/server/rest/services/"
        "AgricultureCensus/"
        "India_Agriculture_Statistics_2022_2023_Wheat_Production/"
        "MapServer/0"
    ),

    "Maize": (
        "https://livingatlas.esri.in/server/rest/services/"
        "AgricultureCensus/"
        "India_Agriculture_Statistics_2022_2023_Maize_Production/"
        "MapServer/0"
    ),

    "Urad": (
        "https://livingatlas.esri.in/server/rest/services/"
        "AgricultureCensus/"
        "India_Agriculture_Statistics_2022_2023_Urad_Production/"
        "MapServer/0"
    ),
}

#download function
def download_layer(crop, layer_url):

    print("\n" + "=" * 70)
    print(f"Downloading UPAg data: {crop}")
    print("=" * 70)

    query_url = layer_url + "/query"

    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json"
    }

    response = requests.get(
        query_url,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(
            f"UPAg API error for {crop}:\n"
            f"{data['error']}"
        )

    features = data.get("features", [])

    if not features:
        raise ValueError(
            f"No records returned for {crop}"
        )

    records = [
        feature["attributes"]
        for feature in features
    ]

    df = pd.DataFrame(records)

    output_path = (
        OUTPUT_DIR
        / f"{crop.lower()}_upag_raw.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(f"Records: {len(df):,}")
    print(f"Saved: {output_path}")

    return df

#Main
def main():

    print("UPAg APY DOWNLOAD")
    print("=================")

    for crop, url in CROP_LAYERS.items():

        try:
            download_layer(
                crop,
                url
            )

        except Exception as e:

            print(
                f"\nERROR downloading {crop}:"
            )

            print(e)


if __name__ == "__main__":
    main()