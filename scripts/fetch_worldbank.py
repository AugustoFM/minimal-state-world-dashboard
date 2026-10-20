"""Download World Bank indicators for all countries -> data/raw/worldbank_long.csv"""
import csv, requests, pathlib
IND = {
 "NY.GDP.MKTP.CD": "gdp_usd",
 "NY.GDP.PCAP.PP.CD": "gdp_pc_ppp",
 "SL.UEM.TOTL.ZS": "unemployment",
 "SH.UHC.SRVS.CV.XD": "uhc_index",
 "SP.DYN.LE00.IN": "life_expectancy",
 "SI.POV.GINI": "gini",
 "SI.DST.10TH.10": "income_top10",
 "GC.XPN.TOTL.GD.ZS": "gov_expense_pct_gdp",
}
OUT = pathlib.Path("data/raw/worldbank_long.csv"); OUT.parent.mkdir(parents=True, exist_ok=True)
countries = {c["id"]: c for c in requests.get("https://api.worldbank.org/v2/country?format=json&per_page=400", timeout=60).json()[1]}
real = {k for k, c in countries.items() if c["region"]["value"] != "Aggregates"}
rows = []
for code, name in IND.items():
    r = requests.get(f"https://api.worldbank.org/v2/country/all/indicator/{code}", params={"format": "json", "per_page": 20000, "date": "2010:2025"}, timeout=120).json()
    for d in r[1] or []:
        if d["value"] is not None and d["countryiso3code"] and d["country"]["id"] in real:
            rows.append((d["countryiso3code"], d["country"]["value"], name, d["date"], d["value"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["iso3", "country", "indicator", "year", "value"]); w.writerows(rows)
print(len(rows), "rows ->", OUT)
