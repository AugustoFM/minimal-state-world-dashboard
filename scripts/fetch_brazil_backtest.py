"""Fetch observed Brazil macro series for the D2 back-tests (2003-2015, 2017-2022).

Downloads untouched API responses into data/raw/brazil/backtest/ (World Bank WDI
and Banco Central do Brasil SGS) and builds an annual table
data/brazil/backtest_observed.csv with value, year, series code and source for
every observation. December values are used for BCB monthly series (stocks and
12-month rates); nothing is interpolated. Re-running overwrites the raw files
with a fresh download, so record the retrieval date in data/raw/SOURCES.md.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/backtest"
OUTPUT = ROOT / "data/brazil/backtest_observed.csv"
FIRST_YEAR, LAST_YEAR = 2000, 2024

WORLD_BANK = {
    "NY.GDP.MKTP.KD.ZG": ("gdp_growth_pct", "GDP growth, constant prices (%)"),
    "NE.CON.PRVT.KD.ZG": ("household_consumption_growth_pct", "Household final consumption growth (%)"),
    "SL.UEM.TOTL.ZS": ("unemployment_ilo_pct", "Unemployment, ILO modelled estimate (%)"),
    "NE.EXP.GNFS.CD": ("exports_usd", "Exports of goods and services (current US$)"),
    "FI.RES.TOTL.CD": ("reserves_usd", "Total reserves incl. gold (current US$)"),
    "DT.DOD.DECT.CD": ("external_debt_usd", "External debt stocks, total (current US$)"),
    "DT.DOD.DECT.GN.ZS": ("external_debt_pct_gni", "External debt stocks (% of GNI)"),
    "BX.KLT.DINV.CD.WD": ("fdi_net_inflows_usd", "FDI, net inflows (current US$)"),
    "FP.CPI.TOTL.ZG": ("cpi_inflation_pct", "Inflation, consumer prices (%)"),
    "PA.NUS.FCRF": ("brl_per_usd", "Official exchange rate, period average"),
    "TT.PRI.MRCH.XD.WD": ("net_barter_terms_of_trade", "Net barter terms of trade index (2015 = 100)"),
    "SI.POV.GINI": ("gini_wb", "Gini index (World Bank estimate)"),
}
# BCB SGS series; December observation is taken for each year.
BCB = {
    4189: ("selic_pct", "Selic rate, monthly annualised (% p.a.), December"),
    13522: ("ipca_12m_pct", "IPCA, 12-month change (%), December"),
    5793: ("primary_result_pct_gdp", "Public sector borrowing requirement, primary, consolidated public sector, 12-month (% GDP), December; negative = surplus"),
    4513: ("net_public_debt_pct_gdp", "Net public sector debt (% GDP), December"),
    13762: ("gross_general_government_debt_pct_gdp", "General government gross debt (% GDP), December"),
}


def fetch_json(url: str, path: Path, attempts: int = 4) -> object:
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                body = response.read()
            break
        except (TimeoutError, OSError):
            if attempt == attempts:
                raise
            time.sleep(5 * attempt)
    path.write_bytes(body)
    return json.loads(body)


def world_bank_rows() -> list[dict]:
    rows = []
    for code, (name, label) in WORLD_BANK.items():
        url = (
            f"https://api.worldbank.org/v2/country/BRA/indicator/{code}"
            f"?format=json&date={FIRST_YEAR}:{LAST_YEAR}&per_page=200"
        )
        payload = fetch_json(url, RAW / f"worldbank_{code}.json")
        for record in payload[1] or []:
            if record["value"] is not None:
                rows.append({
                    "year": int(record["date"]), "indicator": name, "value": float(record["value"]),
                    "label": label, "series_code": code, "source": "World Bank WDI API",
                })
    return rows


def bcb_rows() -> list[dict]:
    rows = []
    for code, (name, label) in BCB.items():
        url = (
            f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados?formato=json"
            f"&dataInicial=01/01/{FIRST_YEAR}&dataFinal=31/12/{LAST_YEAR}"
        )
        payload = fetch_json(url, RAW / f"bcb_sgs_{code}.json")
        for record in payload:
            if record["data"].startswith("01/12"):
                rows.append({
                    "year": int(record["data"][-4:]), "indicator": name, "value": float(record["valor"]),
                    "label": label, "series_code": f"SGS {code}", "source": "Banco Central do Brasil SGS API",
                })
    return rows


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(world_bank_rows() + bcb_rows()).sort_values(["indicator", "year"])
    if table.duplicated(["indicator", "year"]).any():
        raise ValueError("Duplicate indicator-year observations")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(table)} observations ({table['indicator'].nunique()} indicators) to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
