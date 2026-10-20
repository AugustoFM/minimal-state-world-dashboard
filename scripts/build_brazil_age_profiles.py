"""Build Brazil single-age public-spending profiles from the archived NTA file."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SHEET = "Per capita Normalized"
PROFILE_ACCOUNTS = {
    "pension": "Public Transfers, Pensions  (RGPS), Inflows",
    "health": "Public Transfers, Health, Inflows",
    "education": "Public Transfers, Education, Inflows",
}
PROFILE_YEARS = (2003, 2018)


def build_profiles(workbook: str | Path) -> pd.DataFrame:
    """Extract the requested NTA accounts without rescaling their values."""
    source_path = Path(workbook)
    raw = pd.read_excel(source_path, sheet_name=SHEET, header=1)
    required = {"Year", "AccountName", *range(91)}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"NTA sheet {SHEET!r} is missing columns: {sorted(missing, key=str)}")

    records: list[dict] = []
    for year in PROFILE_YEARS:
        for category, account in PROFILE_ACCOUNTS.items():
            match = raw.loc[raw["Year"].eq(year) & raw["AccountName"].eq(account)]
            if len(match) != 1:
                raise ValueError(
                    f"Expected one row for year={year}, account={account!r}; "
                    f"found {len(match)}"
                )
            row = match.iloc[0]
            excel_row = int(match.index[0]) + 3
            for age in range(91):
                value = pd.to_numeric(row[age], errors="raise")
                if pd.isna(value) or value < 0:
                    raise ValueError(
                        f"Invalid value for year={year}, account={account!r}, age={age}"
                    )
                records.append(
                    {
                        "category": category,
                        "age": age,
                        "relative_cost_per_capita": float(value),
                        "profile_year": year,
                        "account": account,
                        "source": (
                            f"NTA_Brasil.xlsx, sheet '{SHEET}', row {excel_row}; "
                            "per-capita normalized value"
                        ),
                        # The RGPS profile is applied to COFOG old-age plus survivors,
                        # which also covers RPPS. The workbook does not identify RPPS
                        # inside its undifferentiated Other cash account.
                        "is_proxy": category == "pension",
                    }
                )
    return pd.DataFrame.from_records(records)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="data/raw/brazil/age_profiles/NTA_Brasil.xlsx",
    )
    parser.add_argument("--output", default="data/brazil/age_profiles.csv")
    args = parser.parse_args(argv)

    profiles = build_profiles(args.input)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(output, index=False, float_format="%.15g")
    print(f"Wrote {len(profiles)} single-age profile rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
