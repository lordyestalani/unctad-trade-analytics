"""Read and validate the reporting subset without modifying the source CSV."""

import argparse
from pathlib import Path

import pandas as pd


COUNTRIES = {
    "360": "Indonesia",
    "458": "Malaysia",
    "608": "Philippines",
    "704": "Viet Nam",
    "764": "Thailand",
}
FLOWS = {"01": "Imports", "02": "Exports"}
YEARS = range(2015, 2025)
MEASURES = [
    "Millions of US$ at current prices",
    "Percentage of total world",
    "Growth rate, year-on-year",
]
KEY = ["Economy", "Year", "Flow"]
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data/raw/US_TradeMerchTotal.csv"


def read_and_validate(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, dtype={"Economy": "string", "Flow": "string"})
    required = KEY + ["Economy Label", "Flow Label"] + MEASURES
    missing = sorted(set(required) - set(data.columns))
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")

    data["Year"] = pd.to_numeric(data["Year"], errors="raise")
    subset = data.loc[
        data["Economy"].isin(COUNTRIES) & data["Year"].isin(YEARS)
    ].copy()

    if subset.duplicated(KEY).any():
        raise ValueError("Duplicate country-year-flow records found.")

    expected = pd.MultiIndex.from_product([COUNTRIES, YEARS, FLOWS], names=KEY)
    actual = pd.MultiIndex.from_frame(subset[KEY])
    if len(expected.difference(actual)) or len(actual.difference(expected)):
        raise ValueError("Expected all 100 country-year-flow combinations for 2015-2024.")

    if not subset["Economy Label"].eq(subset["Economy"].map(COUNTRIES)).all():
        raise ValueError("Country labels do not match their codes.")
    if not subset["Flow Label"].eq(subset["Flow"].map(FLOWS)).all():
        raise ValueError("Flow labels do not match their codes.")

    for column in MEASURES:
        values = pd.to_numeric(subset[column], errors="raise")
        if values.isna().any() or values.isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"Missing or non-finite values in {column}.")
        subset[column] = values

    return subset.sort_values(KEY).reset_index(drop=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    try:
        trade = read_and_validate(args.path)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        parser.exit(1, f"Validation failed: {error}\n")

    print(f"Validation passed: {len(trade)} records, 5 countries, 2015-2024, exports and imports.")
    print("No duplicate keys or missing/non-finite measures. Codes and labels match.")
    print(trade.groupby(["Economy Label", "Flow Label"]).size().to_string(name="Records"))
