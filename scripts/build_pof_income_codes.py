"""Classify POF 2017-2018 income-type codes (V9001) for the microsimulation (C3).

Codes and descriptions are read from the official product register inside
data/raw/brazil/layouts/pof_2017_2018_documentation.zip ('Cadastro de
Produtos.xls'), quadros 53 (work), 54 (monthly other income) and 55 (annual and
occasional receipts). Only the category assignment below is ours: it is a
lead-developer classification (2026-10-20) to review, not an IBGE grouping.
`scenario_package` links a code to the config/scenarios.yaml package category
that a spending change would act on; empty means no direct link.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "data/raw/brazil/layouts/pof_2017_2018_documentation.zip"
OUTPUT = ROOT / "data/brazil/micro/mappings/pof_2017_2018_income_codes.csv"
INCOME_QUADROS = {"53", "54", "55"}

# category -> (scenario_package, codes). Codes not listed fall back by quadro.
CATEGORIES: dict[str, tuple[str, set[str]]] = {
    "bolsa_familia": ("means_tested_transfers", {"5400101", "5400102", "5400103", "5506601"}),
    "bpc_loas": ("means_tested_transfers", {"5400201"}),
    "other_social_programs": ("means_tested_transfers", {
        "5400104", "5400105", "5400106", "5400107", "5400108", "5400301", "5400302", "5400303",
        "5400304", "5400305", "5400306", "5400307", "5400308", "5400309", "5400310", "5400311",
        "5400312", "5400314", "5400315", "5400316", "5400317", "5402701", "5503603", "5505601",
        "5506501",
    }),
    "public_pension_inss": ("pension_and_indexation", {"5400401", "5400501", "5500301", "5500401"}),
    "public_pension_civil_servants": ("pension_and_indexation", {"5400601", "5400701", "5500501", "5500601"}),
    "other_social_insurance": ("pension_and_indexation", {
        "5400901", "5403001", "5503601", "5504501", "5506201", "5400313", "5504601",
    }),
    "unemployment_insurance_and_abono": ("other_current", {"5501701", "5501702", "5501801", "5500801", "5500901"}),
    "private_pension": ("", {"5400801", "5402901", "5500701", "5503301", "5504701"}),
    "foreign_public_pension": ("", {"5403101", "5506401"}),
    "private_transfers": ("", {"5401101", "5401201", "5401301", "5505401", "5506301", "5505701"}),
    "property_income": ("", {"5401401", "5401501", "5401502", "5504801", "5506001", "5504401"}),
    "work_fringe_benefits": ("", {
        "5401601", "5401701", "5402001", "5402002", "5402003", "5402004", "5402005", "5402006",
        "5402007", "5402008", "5402101", "5402201", "5402301", "5402401", "5402501", "5402601",
        "5402602", "5402603", "5402604", "5402801", "5403201", "5403301", "5403401",
    }),
    "work_annual_and_occasional": ("", {
        "5500101", "5500102", "5500103", "5500201", "5501101", "5501201", "5501301", "5501401",
        "5501402", "5501501", "5503801", "5503901", "5503902", "5503903", "5504001", "5504002",
        "5504101", "5504201", "5504301", "5505301", "5505801", "5505802",
    }),
    "not_current_income": ("", {
        "5501001", "5501601", "5501602", "5502001", "5503201", "5503501", "5506101",
        "5503701", "5505501",
    }),
}


def read_register() -> pd.DataFrame:
    with zipfile.ZipFile(DOCS) as archive:
        name = next(n for n in archive.namelist() if n.startswith("Cadastro de Produtos.xls"))
        raw = archive.read(name)
    register = pd.read_excel(io.BytesIO(raw), header=None, dtype=str).iloc[1:]
    register.columns = ["quadro", "code", "description"]
    register["quadro"] = register["quadro"].str.strip()
    register["code"] = register["code"].str.strip()
    return register.loc[register["quadro"].isin(INCOME_QUADROS)].reset_index(drop=True)


def classify(code: str, quadro: str, description: str) -> tuple[str, str]:
    for category, (package, codes) in CATEGORIES.items():
        if code in codes:
            return category, package
    if quadro == "53":
        return "labor_income", ""
    upper = description.upper()
    if upper.startswith("VENDA DE") or "RESTITUICAO" in upper or "DEVOLUCAO" in upper or "INDENIZACAO" in upper:
        return "not_current_income", ""
    return "other_income", ""


def build() -> pd.DataFrame:
    register = read_register()
    labels = [classify(c, q, d) for c, q, d in zip(register["code"], register["quadro"], register["description"])]
    register["category"] = [c for c, _ in labels]
    register["scenario_package"] = [p for _, p in labels]
    register["classified_by"] = "Claude 2026-10-20 (review before C3 use)"
    return register


def main() -> int:
    codes = build()
    unknown = sorted(set().union(*(c for _, c in CATEGORIES.values())) - set(codes["code"]))
    if unknown:
        raise ValueError(f"Classification lists codes absent from the register: {unknown}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    codes.to_csv(OUTPUT, index=False)
    print(codes.groupby(["category", "scenario_package"], dropna=False).size().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
