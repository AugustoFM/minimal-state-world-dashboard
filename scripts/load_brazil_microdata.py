"""Load selected, identifier-free exports from IBGE household surveys.

Raw PNAD Contínua and POF text files require their accompanying IBGE layouts
and reading programs. This loader deliberately accepts only CSV/Parquet exports
made with those official programs and only columns explicitly mapped by a
reviewed JSON file. It does not download or unpack microdata.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ALLOWED_DATASETS = {"pnadc", "pof"}
FORBIDDEN_COLUMN = re.compile(
    r"cpf|cnpj|nome|endere[cç]o|telefone|email|person.?id|household.?id|sample.?id|cluster.?id|"
    r"(?:^|_)(?:cod_)?upa$|num_dom|num_uc|^v1008$|^v1014$",
    re.I,
)
ALLOWED_CANONICAL = {
    "year", "state_code", "urban_rural", "sex", "age", "education_level",
    "labor_force_status", "employment_status",
    "labor_income_nominal_brl", "labor_income_real_brl", "household_income_brl",
    "household_income_per_capita_brl", "consumption_expenditure_brl", "survey_weight",
}


def load_export(dataset: str, input_path: Path, mapping_path: Path) -> pd.DataFrame:
    dataset = dataset.lower()
    if dataset not in ALLOWED_DATASETS:
        raise ValueError(f"dataset must be one of {sorted(ALLOWED_DATASETS)}")
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    if mapping.get("dataset") != dataset:
        raise ValueError("mapping dataset does not match the selected survey")
    columns = mapping.get("columns", {})
    if not columns or not isinstance(columns, dict):
        raise ValueError("mapping must provide a non-empty source-column to canonical-name map")
    bad_targets = set(columns.values()) - ALLOWED_CANONICAL
    if bad_targets:
        raise ValueError(f"unsupported canonical fields: {sorted(bad_targets)}")
    if any(FORBIDDEN_COLUMN.search(name) for name in columns):
        raise ValueError("source mapping includes a direct identifier or personal identifier field")
    if any(FORBIDDEN_COLUMN.search(name) for name in columns.values()):
        raise ValueError("canonical mapping includes an identifier field")
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(input_path, low_memory=False)
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(input_path)
    else:
        raise ValueError("input must be a CSV or Parquet export produced using the official IBGE reading layout")
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"source columns absent from export: {sorted(missing)}")
    result = frame[list(columns)].rename(columns=columns).copy()
    if "year" not in result or "survey_weight" not in result:
        raise ValueError("mapping must include year and survey_weight")
    result.insert(0, "survey", "PNAD Continua" if dataset == "pnadc" else "POF 2017-2018")
    result.insert(1, "source_file", input_path.name)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=sorted(ALLOWED_DATASETS))
    parser.add_argument("input", type=Path, help="CSV/Parquet export generated from official IBGE layout")
    parser.add_argument("mapping", type=Path, help="Reviewed JSON source-to-canonical column mapping")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = load_export(args.dataset, args.input, args.mapping)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    print(f"Wrote {len(data)} rows to {args.output}")


if __name__ == "__main__":
    main()
