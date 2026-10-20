"""Merge all raw sources into data/processed/countries.csv (one row per ISO3). Run from repo root."""
import json, re, pandas as pd, pycountry
R = "data/raw/"

# ---- World Bank: latest non-null value per country/indicator, keep year
wb = pd.read_csv(R + "worldbank_long.csv").sort_values("year")
last = wb.groupby(["iso3", "country", "indicator"]).tail(1)
w = last.pivot(index=["iso3", "country"], columns="indicator", values=["value", "year"])
w.columns = [f"{b}_year" if a == "year" else b for a, b in w.columns]
df = w.reset_index()

# ---- Fraser EFW 2026 (data year 2024)
e = pd.read_excel(R + "efotw-2026-master-index-data-for-researchers-iso.xlsx", sheet_name="EFW Ratings", header=3)
e = e[e["Year"] == 2024]
pick = {"ISO_Code": "iso3", "ECONOMIC FREEDOM ALL AREAS": "efw_overall", "EFW RANK": "efw_rank",
        "1A Government consumption": "efw_1a_consumption", "1B  Transfers and subsidies": "efw_1b_transfers",
        "1C  Government investment": "efw_1c_investment", "1D  Top marginal tax rate": "efw_1d_tax",
        "IE State ownership": "efw_1e_state_ownership", "Area 1 Size of Government": "efw_area1_size"}
e = e[[c for c in pick if c in e.columns]].rename(columns=pick)
for c in e.columns:
    if c.startswith("efw_") and c != "efw_rank": e[c] = pd.to_numeric(e[c], errors="coerce")
df = df.merge(e, on="iso3", how="outer")

# ---- Heritage 2026 (names -> ISO3)
h = pd.read_csv(R + [f for f in __import__("os").listdir(R) if f.startswith("heritage")][0], skiprows=4, na_values=["N/A"])
alias = {"Korea, South": "KOR", "Korea, North": "PRK", "Russia": "RUS", "Taiwan": "TWN", "Hong Kong": "HKG", "Macau": "MAC",
         "Burma": "MMR", "Congo, Democratic Republic of the Congo": "COD", "Congo, Republic of": "COG", "Cabo Verde": "CPV",
         "Czech Republic": "CZE", "Czechia": "CZE", "Cote d'Ivoire": "CIV", "Côte d'Ivoire": "CIV", "Gambia, The": "GMB",
         "Bahamas, The": "BHS", "Kyrgyz Republic": "KGZ", "Slovak Republic": "SVK", "Turkey": "TUR", "Vietnam": "VNM", "Laos": "LAO",
         "Eswatini": "SWZ", "Democratic Republic of Congo": "COD", "Republic of Congo": "COG", "São Tomé and Príncipe": "STP", "The Bahamas": "BHS", "The Gambia": "GMB", "The Philippines": "PHL", "Brunei": "BRN", "Hong Kong": "HKG", "Puerto Rico": "PRI", "Macao": "MAC", "Macau": "MAC", "West Bank": "PSE", "Palestine": "PSE", "Iran": "IRN", "Syria": "SYR", "Venezuela": "VEN", "Bolivia": "BOL", "Tanzania": "TZA",
         "Micronesia": "FSM", "Sao Tome and Principe": "STP", "Timor-Leste": "TLS", "Kosovo": "XKX", "North Macedonia": "MKD"}
def iso(n):
    n = str(n).strip()
    if n in alias: return alias[n]
    try: return pycountry.countries.lookup(n).alpha_3
    except LookupError: return None
h["iso3"] = h["Country"].map(iso)
print("Heritage names without ISO:", h[h.iso3.isna()]["Country"].tolist())
h = h.dropna(subset=["iso3"]).rename(columns={"Overall Score": "heritage_overall", "Government Spending": "heritage_gov_spending",
        "Tax Burden": "heritage_tax_burden", "Fiscal Health": "heritage_fiscal_health", "Property Rights": "heritage_property_rights"})
h = h[["iso3", "heritage_overall", "heritage_gov_spending", "heritage_tax_burden", "heritage_fiscal_health", "heritage_property_rights"]]
df = df.merge(h, on="iso3", how="outer")

# ---- UNDP HDI (latest year)
j = pd.DataFrame(json.load(open(R + "hdr-data.json")))
j["value"] = pd.to_numeric(j["actualValue"], errors="coerce"); j["year"] = pd.to_numeric(j["year"])
hd = j[j.indicatorCode.isin(["hdi", "eys", "mys"])].dropna(subset=["value"]).sort_values("year").groupby(["countryIsoCode", "indicatorCode"]).tail(1)
hd = hd.pivot(index="countryIsoCode", columns="indicatorCode", values="value").rename(columns={"hdi": "hdi", "eys": "expected_schooling", "mys": "mean_schooling"})
hy = j[j.indicatorCode == "hdi"].dropna(subset=["value"]).groupby("countryIsoCode")["year"].max().rename("hdi_year")
df = df.merge(hd.join(hy).reset_index().rename(columns={"countryIsoCode": "iso3"}), on="iso3", how="outer")


# ---- Freedom House ratings (PR/CL 1-7, 1 = freest; latest edition in the file = FIW 2025, covering 2024)
fh = pd.concat([pd.read_excel(R + "freedom_house_country_scores.xlsx", sheet_name=i, header=None).iloc[3:, [0, -3, -2, -1]] for i in (1, 2)])  # countries + territories
fh.columns = ["name", "fh_pr", "fh_cl", "fh_status"]
fh_alias = {"Brunei": "BRN", "Hong Kong": "HKG", "Puerto Rico": "PRI", "Macao": "MAC", "Macau": "MAC", "West Bank": "PSE", "Palestine": "PSE", "Congo (Brazzaville)": "COG", "Congo (Kinshasa)": "COD", "Cote d'Ivoire": "CIV", "Kosovo": "XKX",
            "Micronesia": "FSM", "Russia": "RUS", "St. Kitts and Nevis": "KNA", "St. Lucia": "LCA",
            "St. Vincent and the Grenadines": "VCT", "The Gambia": "GMB", "Turkey": "TUR"}
def fh_iso(n):
    n = str(n).strip()
    if n in fh_alias: return fh_alias[n]
    try: return pycountry.countries.lookup(n).alpha_3
    except LookupError: return None
fh["iso3"] = fh["name"].map(fh_iso)
fh = fh.dropna(subset=["iso3"])
for c in ("fh_pr", "fh_cl"): fh[c] = pd.to_numeric(fh[c], errors="coerce")
fh = fh.dropna(subset=["fh_pr", "fh_cl"])
fh["fh_rights_index"] = ((7 - fh["fh_pr"]) + (7 - fh["fh_cl"])) / 12 * 100   # derived 0-100, 100 = freest
df = df.merge(fh[["iso3", "fh_pr", "fh_cl", "fh_status", "fh_rights_index"]], on="iso3", how="left")

# ---- UBS Global Wealth Report 2026 (partial: ~34 countries)
df = df.merge(pd.read_csv(R + "ubs_gwr2026_extracted.csv"), on="iso3", how="left")

# ---- names for rows that only came from non-WB sources, drop aggregates / non-countries
names = {c.alpha_3: c.name for c in pycountry.countries}
df["country"] = df["country"].fillna(df["iso3"].map(names))
df = df[df["country"].notna() & df["iso3"].str.match(r"^[A-Z]{3}$", na=False)]
df.to_csv("data/processed/countries.csv", index=False)
print(df.shape, "countries ->", "data/processed/countries.csv")
