"""Fetch observed external-channel series for task C7 (external block v2).

Downloads untouched responses into data/raw/brazil/external/ and builds the
annual table data/brazil/external_observed.csv (year, indicator, value, label,
series_code, source, aggregation). Nothing is interpolated; partial years are
flagged in `aggregation`. Re-running overwrites the raw files with a fresh
download, so record the retrieval date in data/raw/SOURCES.md.

Sources
- IMF Commodity Terms of Trade database (Gruss and Kebhaj 2019, IMF WP 19/21),
  via the DB.nomics API, Brazil, annual, rolling weights.
- J.P. Morgan EMBI+ Brazil spread (basis points), via Ipeadata (JPM366_EMBI366), daily.
- FRED: 10-year US Treasury yield (DGS10, daily) and effective federal funds rate (FEDFUNDS, monthly).
- World Bank WDI: China import volume (from 2005) and value, China GDP growth, world GDP growth, Brazil investment,
  real export/import growth, current account and FDI.
Government property income (dividends, concessions incl. oil royalties) is read
by C7 from the archived Tesouro GFS workbook (data/raw/brazil/demonstrativos-governo-geral.xlsx).
"""
from __future__ import annotations

import csv
import io
import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/external"
OUTPUT = ROOT / "data/brazil/external_observed.csv"
FIRST_YEAR, LAST_YEAR = 1995, 2024

PCTOT = {
    "A.BR.xm_gdp.H_RW_IX": ("commodity_tot_index", "Commodity net export price index, weights = net exports/GDP, rolling (Gruss-Kebhaj CTOT)"),
    "A.BR.x.H_RW_IX": ("commodity_export_price_index", "Commodity export price index, weights = exports/total commodity exports, rolling"),
    "A.BR.m.H_RW_IX": ("commodity_import_price_index", "Commodity import price index, weights = imports/total commodity imports, rolling"),
}
WORLD_BANK = {
    ("CHN", "TM.QTY.MRCH.XD.WD"): ("china_import_volume_index", "China merchandise import volume index (2015 = 100); WDI coverage from 2005"),
    ("CHN", "TM.VAL.MRCH.CD.WT"): ("china_merchandise_imports_usd", "China merchandise imports (current US$)"),
    ("CHN", "NY.GDP.MKTP.KD.ZG"): ("china_gdp_growth_pct", "China GDP growth, constant prices (%)"),
    ("WLD", "NY.GDP.MKTP.KD.ZG"): ("world_gdp_growth_pct", "World GDP growth, constant prices (%)"),
    ("BRA", "NE.GDI.FTOT.ZS"): ("investment_rate_pct_gdp", "Brazil gross fixed capital formation (% of GDP)"),
    ("BRA", "NE.GDI.FTOT.KD.ZG"): ("investment_volume_growth_pct", "Brazil gross fixed capital formation, constant prices (% growth)"),
    ("BRA", "NE.EXP.GNFS.KD.ZG"): ("export_volume_growth_pct", "Brazil exports, constant prices (% growth)"),
    ("BRA", "NE.IMP.GNFS.KD.ZG"): ("import_volume_growth_pct", "Brazil imports, constant prices (% growth)"),
    ("BRA", "BN.CAB.XOKA.GD.ZS"): ("current_account_pct_gdp", "Brazil current account balance (% of GDP)"),
    ("BRA", "BX.KLT.DINV.WD.GD.ZS"): ("fdi_net_inflows_pct_gdp", "Brazil FDI net inflows (% of GDP)"),
}


def fetch(url: str, path: Path, attempts: int = 5) -> bytes:
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "minimal-state-dashboard/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read()
            break
        except (TimeoutError, OSError):
            if attempt == attempts:
                raise
            time.sleep(10 * attempt)
    path.write_bytes(body)
    return body


def rows_pctot() -> list[dict]:
    rows = []
    for code, (name, label) in PCTOT.items():
        body = fetch(f"https://api.db.nomics.world/v22/series/IMF/PCTOT/{code}?observations=1", RAW / f"imf_pctot_{code}.json")
        doc = json.loads(body)["series"]["docs"][0]
        for period, value in zip(doc["period"], doc["value"]):
            if value != "NA" and FIRST_YEAR <= int(period) <= LAST_YEAR:
                rows.append(dict(year=int(period), indicator=name, value=float(value), label=label,
                                 series_code=f"IMF/PCTOT/{code}", source="IMF Commodity Terms of Trade database via DB.nomics",
                                 aggregation="annual"))
    return rows


def rows_embi() -> list[dict]:
    body = fetch("http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='JPM366_EMBI366')", RAW / "ipeadata_JPM366_EMBI366.json")
    frame = pd.DataFrame(json.loads(body)["value"])
    frame["date"] = pd.to_datetime(frame["VALDATA"].str[:10])
    frame = frame.dropna(subset=["VALVALOR"])
    rows = []
    for year, group in frame.groupby(frame["date"].dt.year):
        if FIRST_YEAR <= year <= LAST_YEAR:
            last_month = int(group["date"].dt.month.max())
            rows.append(dict(year=int(year), indicator="embi_brazil_spread_bp", value=float(group["VALVALOR"].mean()),
                             label="EMBI+ Brazil sovereign spread, annual mean of daily values (bp)",
                             series_code="JPM366_EMBI366", source="J.P. Morgan via Ipeadata",
                             aggregation="annual mean" if last_month == 12 else f"partial-year mean (to month {last_month})"))
    return rows


def rows_fred() -> list[dict]:
    rows = []
    for code, name, label in [
        ("DGS10", "us_10y_yield_pct", "US 10-year Treasury constant-maturity yield, annual mean (%)"),
        ("FEDFUNDS", "us_fed_funds_pct", "US effective federal funds rate, annual mean (%)"),
    ]:
        body = fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}", RAW / f"fred_{code}.csv")
        frame = pd.read_csv(io.BytesIO(body), na_values=["."])
        frame.columns = ["date", "value"]
        frame["date"] = pd.to_datetime(frame["date"])
        frame = frame.dropna()
        for year, group in frame.groupby(frame["date"].dt.year):
            if FIRST_YEAR <= year <= LAST_YEAR:
                rows.append(dict(year=int(year), indicator=name, value=float(group["value"].mean()), label=label,
                                 series_code=code, source="Federal Reserve Bank of St. Louis (FRED)", aggregation="annual mean"))
    return rows


def rows_world_bank() -> list[dict]:
    rows = []
    for (country, code), (name, label) in WORLD_BANK.items():
        url = (f"https://api.worldbank.org/v2/country/{country}/indicator/{code}"
               f"?format=json&per_page=200&date={FIRST_YEAR}:{LAST_YEAR}")
        body = fetch(url, RAW / f"wdi_{country}_{code}.json")
        for entry in json.loads(body)[1] or []:
            if entry["value"] is not None:
                rows.append(dict(year=int(entry["date"]), indicator=name, value=float(entry["value"]), label=label,
                                 series_code=f"{country}:{code}", source="World Bank WDI API", aggregation="annual"))
    return rows


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    rows = rows_pctot() + rows_embi() + rows_fred() + rows_world_bank()
    table = pd.DataFrame(rows).sort_values(["indicator", "year"]).reset_index(drop=True)
    if table.duplicated(["indicator", "year"]).any():
        raise RuntimeError("duplicate indicator-year rows")
    table.to_csv(OUTPUT, index=False, quoting=csv.QUOTE_MINIMAL, float_format="%.10g")
    print(f"{len(table)} rows, {table['indicator'].nunique()} indicators -> {OUTPUT}")
    print(table.groupby("indicator")["year"].agg(["min", "max", "count"]).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
