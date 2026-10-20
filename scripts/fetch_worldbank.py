"""Download World Bank indicators for all countries -> data/raw/worldbank_long.csv"""
import csv, time, pathlib, requests

IND = {
    "NY.GDP.MKTP.CD": "gdp_usd",
    "NY.GDP.PCAP.PP.CD": "gdp_pc_ppp",
    "SL.UEM.TOTL.ZS": "unemployment",
    "SH.MED.PHYS.ZS": "physicians_per_1000",   # health-access proxy
    "SH.MED.BEDS.ZS": "hospital_beds_per_1000",  # health-access proxy
    "SH.XPD.CHEX.GD.ZS": "health_spend_pct_gdp",
    "SP.DYN.LE00.IN": "life_expectancy",
    "SI.POV.GINI": "gini",
    "SI.DST.10TH.10": "income_top10",
    "GC.XPN.TOTL.GD.ZS": "gov_expense_pct_gdp",
    "GOV_WGI_VA.EST": "voice_accountability",   # WGI, civil/political rights proxy (-2.5..2.5)
    "GOV_WGI_RL.EST": "rule_of_law",            # WGI (-2.5..2.5)
}
WGI = set()  # WGI codes now carry the GOV_WGI_ prefix and need no source parameter
# UHC service coverage index code (SH.UHC.SRVS.CV.XD) is archived in the API; take it from the WHO/UNDP files in task T3.
BASE = "https://api.worldbank.org/v2"
OUT = pathlib.Path("data/raw/worldbank_long.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)


def get(url, params, tries=4):
    """GET returning parsed JSON, retrying; raises with the API's own message if the reply is an error."""
    for i in range(tries):
        try:
            r = requests.get(url, params={**params, "format": "json"}, timeout=120)
            j = r.json()
            if isinstance(j, list) and len(j) >= 2 and j[1] is not None:
                return j
            msg = j[0] if isinstance(j, list) and j else j
            print("  API reply without data:", msg)
        except Exception as e:
            print("  request failed:", e)
        time.sleep(2 * (i + 1))
    return None


meta = get(f"{BASE}/country", {"per_page": 400})
if meta is None:
    raise SystemExit("Could not download the country list")
real = {c["id"] for c in meta[1] if c["region"]["value"] != "Aggregates"}  # ISO3 codes

rows = []
for code, name in IND.items():
    print("Fetching", code, name)
    page, pages = 1, 1
    while page <= pages:
        j = get(f"{BASE}/country/all/indicator/{code}", {"per_page": 5000, "page": page, "date": "2010:2025", **({"source": 3} if code in WGI else {})})
        if j is None:
            print("  SKIPPED", code)
            break
        pages = j[0]["pages"]
        for d in j[1]:
            if d["value"] is not None and d["countryiso3code"] in real:
                rows.append((d["countryiso3code"], d["country"]["value"], name, d["date"], d["value"]))
        page += 1

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "country", "indicator", "year", "value"])
    w.writerows(rows)
print(len(rows), "rows ->", OUT)
