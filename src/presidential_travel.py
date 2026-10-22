"""Brazilian presidential travel, cost, FDI and export analysis.

Run from the repository root with ``python -m src.presidential_travel``.
All inputs are local snapshots.  The module never downloads data and writes only
the outputs listed in tasks/TR.md.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_TRAVEL = ROOT / "data/raw/brazil/travel"
RAW_RATES = ROOT / "data/raw/brazil/rates"
RAW_EXTERNAL = ROOT / "data/raw/brazil/external_sector"
DATA_DIR = ROOT / "data/brazil"
OUTPUT_DIR = ROOT / "outputs/presidential_travel"
AS_OF = date(2026, 10, 22)

TRIPS_OUT = DATA_DIR / "presidential_trips.csv"
COSTS_OUT = DATA_DIR / "presidential_travel_costs.csv"
ESTIMATES_OUT = DATA_DIR / "travel_trade_estimates.csv"
REPORT_OUT = ROOT / "outputs/presidential_travel.md"
METHOD_OUT = ROOT / "docs/presidential_travel.md"
HTML_OUT = OUTPUT_DIR / "presidential_travel.html"

SUPPORT_LOWER_BOUND_LABEL = (
    "LOWER BOUND — travel-system support records only; excludes Air Force aircraft, "
    "payment-card hotel/expense items and unitemised costs of the President and spouse"
)

# Frozen page-lead/table cross-checks requested in the review. These are context,
# not substitutes for the consistently grouped trip records produced below.
COUNT_CONTEXT = {
    "FHC": "Press: 108 trips / 347 days",
    "Jair Bolsonaro": "Page lead: 29 trips; archived table: 24",
    "Lula III": "Page lead: 42 trips; archived table: 48",
}

PRESIDENTS = [
    ("FHC", date(1995, 1, 1), date(2002, 12, 31)),
    ("Lula I-II", date(2003, 1, 1), date(2010, 12, 31)),
    ("Dilma Rousseff", date(2011, 1, 1), date(2016, 8, 30)),
    ("Michel Temer", date(2016, 8, 31), date(2018, 12, 31)),
    ("Jair Bolsonaro", date(2019, 1, 1), date(2022, 12, 31)),
    ("Lula III", date(2023, 1, 1), date(2026, 12, 31)),
]

PRIMARY_FILES = {
    "FHC": "wikipedia_pt_viagens_Fernando_Henrique_Cardoso.wikitext",
    "Lula": "wikipedia_pt_viagens_Lula.wikitext",
    "Dilma Rousseff": "wikipedia_trips_Dilma_Rousseff.wikitext",
    "Michel Temer": "wikipedia_trips_Michel_Temer.wikitext",
    "Jair Bolsonaro": "wikipedia_trips_Jair_Bolsonaro.wikitext",
}
SECONDARY_FILES = {
    "Lula": "wikipedia_trips_Luiz_Inacio_Lula_da_Silva.wikitext",
    "Dilma Rousseff": "wikipedia_pt_viagens_Dilma_Rousseff.wikitext",
    "Michel Temer": "wikipedia_pt_viagens_Michel_Temer.wikitext",
    "Jair Bolsonaro": "wikipedia_pt_viagens_Jair_Bolsonaro.wikitext",
}

MONTHS = {
    "january": 1, "jan": 1, "janeiro": 1,
    "february": 2, "feb": 2, "fevereiro": 2,
    "march": 3, "mar": 3, "marco": 3,
    "april": 4, "apr": 4, "abril": 4,
    "may": 5, "maio": 5,
    "june": 6, "jun": 6, "junho": 6,
    "july": 7, "jul": 7, "julho": 7,
    "august": 8, "aug": 8, "agosto": 8,
    "september": 9, "sep": 9, "sept": 9, "setembro": 9,
    "october": 10, "oct": 10, "outubro": 10,
    "november": 11, "nov": 11, "novembro": 11,
    "december": 12, "dec": 12, "dezembro": 12,
}

CODE_COUNTRY = {
    "AFG": "Afghanistan", "AGO": "Angola", "ARG": "Argentina",
    "AUS": "Australia", "AUT": "Austria", "BEL": "Belgium",
    "BHR": "Bahrain", "BOL": "Bolivia", "BWA": "Botswana",
    "BGR": "Bulgaria", "BFA": "Burkina Faso", "CMR": "Cameroon",
    "CAN": "Canada", "CPV": "Cape Verde", "CHL": "Chile", "CHI": "Chile",
    "CHN": "China", "COL": "Colombia", "COD": "Democratic Republic of the Congo",
    "CRI": "Costa Rica", "CUB": "Cuba", "CZE": "Czech Republic",
    "DNK": "Denmark", "DOM": "Dominican Republic", "ECU": "Ecuador",
    "EGY": "Egypt", "SLV": "El Salvador", "GNQ": "Equatorial Guinea",
    "ETH": "Ethiopia", "FIN": "Finland", "FRA": "France",
    "GAB": "Gabon", "DEU": "Germany", "GHA": "Ghana", "GRE": "Greece",
    "GRC": "Greece", "GTM": "Guatemala", "GUA": "Guatemala", "GUY": "Guyana", "HTI": "Haiti",
    "HND": "Honduras", "HUN": "Hungary", "IND": "India", "IDN": "Indonesia",
    "IRN": "Iran", "ISR": "Israel", "ITA": "Italy", "JAM": "Jamaica",
    "JPN": "Japan", "JOR": "Jordan", "KAZ": "Kazakhstan", "KEN": "Kenya",
    "LBN": "Lebanon", "LBY": "Libya", "MAC": "Macao", "MYS": "Malaysia",
    "MEX": "Mexico", "MOZ": "Mozambique", "NAM": "Namibia", "NLD": "Netherlands",
    "NIC": "Nicaragua", "NGA": "Nigeria", "NOR": "Norway", "PAN": "Panama",
    "PRY": "Paraguay", "PAR": "Paraguay", "PER": "Peru", "POL": "Poland",
    "PRT": "Portugal", "POR": "Portugal", "QAT": "Qatar", "ROU": "Romania",
    "RUS": "Russia", "SAU": "Saudi Arabia", "SEN": "Senegal", "SGP": "Singapore",
    "SVK": "Slovakia", "ZAF": "South Africa", "KOR": "South Korea",
    "ESP": "Spain", "SWE": "Sweden", "CHE": "Switzerland", "SUI": "Switzerland",
    "SUR": "Suriname", "TZA": "Tanzania", "TLS": "Timor-Leste", "TUR": "Turkey",
    "UKR": "Ukraine", "ARE": "United Arab Emirates", "GBR": "United Kingdom",
    "USA": "United States", "EUA": "United States", "URY": "Uruguay",
    "URU": "Uruguay", "VAT": "Vatican City", "VEN": "Venezuela", "VNM": "Vietnam",
    "ZMB": "Zambia", "PSE": "Palestine",
}

COUNTRY_ALIASES = {
    "africa do sul": "South Africa", "alemanha": "Germany", "arabia saudita": "Saudi Arabia",
    "argelia": "Algeria", "australia": "Australia", "austria": "Austria",
    "barein": "Bahrain", "belgica": "Belgium", "bolivia": "Bolivia",
    "bulgaria": "Bulgaria", "cabo verde": "Cape Verde", "catar": "Qatar",
    "cazaquistao": "Kazakhstan", "china": "China", "chipre": "Cyprus",
    "colombia": "Colombia", "coreia do sul": "South Korea", "costa rica": "Costa Rica",
    "cuba": "Cuba", "dinamarca": "Denmark", "egito": "Egypt", "emirados arabes unidos": "United Arab Emirates",
    "equador": "Ecuador", "eslovaquia": "Slovakia", "espanha": "Spain",
    "estados unidos": "United States", "estados unidos da america": "United States",
    "etiopia": "Ethiopia", "finlandia": "Finland", "franca": "France",
    "gana": "Ghana", "grecia": "Greece", "guiana": "Guyana", "haiti": "Haiti",
    "hungria": "Hungary", "india": "India", "indonesia": "Indonesia",
    "ira": "Iran", "israel": "Israel", "italia": "Italy", "japao": "Japan",
    "jordania": "Jordan", "libano": "Lebanon", "libia": "Libya", "malasia": "Malaysia",
    "marrocos": "Morocco", "mexico": "Mexico", "mocambique": "Mozambique",
    "namibia": "Namibia", "nigeria": "Nigeria", "noruega": "Norway",
    "nova zelandia": "New Zealand", "paises baixos": "Netherlands",
    "paises baixos holanda": "Netherlands", "panama": "Panama", "paraguai": "Paraguay",
    "peru": "Peru", "polonia": "Poland", "portugal": "Portugal",
    "quenia": "Kenya", "reino unido": "United Kingdom", "republica dominicana": "Dominican Republic",
    "romenia": "Romania", "russia": "Russia", "senegal": "Senegal",
    "singapura": "Singapore", "siria": "Syria", "suecia": "Sweden", "suica": "Switzerland",
    "suriname": "Suriname", "tailandia": "Thailand", "tanzania": "Tanzania",
    "timor leste": "Timor-Leste", "turquia": "Turkey", "ucrania": "Ukraine",
    "uruguai": "Uruguay", "vaticano": "Vatican City", "venezuela": "Venezuela",
    "vietna": "Vietnam",
}


def _ascii(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _plain_wiki(value: str) -> str:
    value = re.sub(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", "", value, flags=re.I | re.S)
    value = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = value.replace("&nbsp;", " ").replace("º", "").replace("ª", "")
    return re.sub(r"\s+", " ", value).strip(" |!")


def president_for_date(value: date | pd.Timestamp) -> str | None:
    d = value.date() if isinstance(value, pd.Timestamp) else value
    for name, start, end in PRESIDENTS:
        if start <= d <= end:
            return name
    return None


def canonical_country(value: object) -> str:
    """Return a stable English country label for cross-source matching."""
    raw = _plain_wiki(str(value))
    raw = re.sub(r"\([^)]*\)", " ", raw)
    key = re.sub(r"[^a-z0-9]+", " ", _ascii(raw)).strip()
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    # English names and common qualifiers.
    english = {
        "united states of america": "United States", "vatican": "Vatican City",
        "south korea": "South Korea", "republic of korea": "South Korea",
        "russian federation": "Russia", "czechia": "Czech Republic",
        "turkiye": "Turkey", "ivory coast": "Cote d'Ivoire",
        "democratic republic of congo": "Democratic Republic of the Congo",
    }
    if key in english:
        return english[key]
    return " ".join(w.capitalize() for w in key.split())


def _extract_country(cell: str) -> str | None:
    candidates = re.findall(r"\{\{\s*(?:flag(?:u|icon)?|flagcountry)\s*\|\s*([^|}]+)", cell, flags=re.I)
    if candidates:
        candidate = candidates[0].strip().upper()
        return CODE_COUNTRY.get(candidate, canonical_country(candidates[0]))
    for token in re.findall(r"\{\{\s*([A-Za-z]{3})(?:b)?(?:\||\}\})", cell):
        if token.upper() in CODE_COUNTRY:
            return CODE_COUNTRY[token.upper()]
    return None


def parse_date_range(value: str, year: int) -> tuple[date, date] | None:
    """Parse the Portuguese/English date forms used by the supplied tables."""
    # Date-link targets are more complete than display labels (and one supplied
    # Temer row has a truncated display label), so prefer the target here.
    value = re.sub(r"\[\[([^\]|]+)\|[^\]]+\]\]", r"\1", value)
    s = _ascii(_plain_wiki(value)).replace("–", "-").replace("—", "-")
    s = re.sub(r"\bde\b", " ", s)
    month_pattern = "|".join(sorted(map(re.escape, MONTHS), key=len, reverse=True))
    found = list(re.finditer(rf"\b({month_pattern})\b", s))
    if not found:
        return None
    if len(found) >= 2:
        m1, m2 = found[0], found[-1]
        before1 = [int(x) for x in re.findall(r"\b([0-3]?\d)\b", s[max(0, m1.start()-18):m1.start()])]
        before2 = [int(x) for x in re.findall(r"\b([0-3]?\d)\b", s[m1.end():m2.start()])]
        if not before1 or not before2:
            return None
        d1, d2 = before1[-1], before2[-1]
        mo1, mo2 = MONTHS[m1.group(1)], MONTHS[m2.group(1)]
    else:
        m = found[0]
        nums = [int(x) for x in re.findall(r"\b([0-3]?\d)\b", s[max(0, m.start()-28):m.start()])]
        if not nums:
            return None
        d1 = nums[-2] if len(nums) >= 2 else nums[-1]
        d2 = nums[-1]
        mo1 = mo2 = MONTHS[m.group(1)]
    try:
        start = date(year, mo1, d1)
        end_year = year + 1 if mo2 < mo1 else year
        end = date(end_year, mo2, d2)
    except ValueError:
        return None
    return start, end


def _table_rows(table: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for block in re.split(r"(?m)^\|-.*$", table)[1:]:
        block = block.split("|}", 1)[0]
        cells: list[str] = []
        for line in block.splitlines():
            if not line.startswith(("|", "!")) or line.startswith(("|-", "|}")):
                continue
            mark = line[0]
            body = line[1:].strip()
            parts = re.split(r"\|\||!!", body)
            for part in parts:
                # Strip cell formatting before its delimiter, preserving wiki-link pipes.
                if re.match(r"^(?:rowspan|colspan|style|class|width|align)\s*=", part, re.I):
                    part = part.split("|", 1)[1] if "|" in part else ""
                cells.append(part.strip())
        if cells:
            rows.append(cells)
    return rows


@dataclass
class VisitRow:
    year: int
    country: str
    start: date
    end: date
    explicit_trip: str | None


def parse_wikitext(text: str, source: str = "memory") -> pd.DataFrame:
    """Parse year tables into one row per country/date entry.

    This deliberately ignores summary and multilateral-event tables: only tables
    within a 1995--2026 year section and rows containing both a country and a date
    enter the result.
    """
    headings = list(re.finditer(r"(?m)^={2,4}\s*(19\d{2}|20\d{2})\s*={2,4}\s*$", text))
    visits: list[VisitRow] = []
    for pos, heading in enumerate(headings):
        year = int(heading.group(1))
        if not 1995 <= year <= 2026:
            continue
        end_pos = headings[pos + 1].start() if pos + 1 < len(headings) else len(text)
        section = text[heading.end():end_pos]
        # The first table after a year heading is the itinerary. Later tables in
        # the same section are summaries/event attendance and must not be trips.
        tables = list(re.finditer(r"\{\|.*?\n\|\}", section, flags=re.S))
        for match in tables[:1]:
            carried_trip: str | None = None
            carried_dates: tuple[date, date] | None = None
            for cells in _table_rows(match.group(0)):
                country = next((_extract_country(c) for c in cells if _extract_country(c)), None)
                dates = next((parse_date_range(c, year) for c in cells if parse_date_range(c, year)), None)
                trip_cell = next((c for c in cells if re.fullmatch(r"(?:'{2,3})?\s*\d{1,3}\s*(?:'{2,3})?", _plain_wiki(c))), None)
                if trip_cell:
                    carried_trip = re.search(r"\d+", trip_cell).group(0)  # type: ignore[union-attr]
                if dates:
                    carried_dates = dates
                if country and carried_dates:
                    visits.append(VisitRow(year, country, carried_dates[0], carried_dates[1], carried_trip))
    return pd.DataFrame([v.__dict__ for v in visits])


def _group_visits(visits: pd.DataFrame, label: str, source_file: str, source_priority: str) -> pd.DataFrame:
    """Collapse country rows into departure-return trips."""
    if visits.empty:
        return pd.DataFrame(columns=["president", "trip_id", "start_date", "end_date", "countries"])
    records: list[dict[str, object]] = []
    for year, group in visits.sort_values(["start", "end"]).groupby("year"):
        if label == "Lula" and 2011 <= year <= 2022:
            continue
        groups: list[list[int]] = []
        numbered = group["explicit_trip"].notna().any()
        if numbered:
            keys: list[str] = []
            fallback = 0
            previous: str | None = None
            for _, row in group.iterrows():
                current = row["explicit_trip"]
                if pd.notna(current):
                    previous = str(current)
                if previous is None:
                    fallback += 1
                    key = f"fallback-{fallback}"
                else:
                    key = previous
                keys.append(key)
            for key in dict.fromkeys(keys):
                groups.append([idx for idx, value in zip(group.index, keys) if value == key])
        else:
            # Lists without trip numbers use overlapping/contiguous itinerary dates.
            current: list[int] = []
            current_end: date | None = None
            for idx, row in group.iterrows():
                if current_end is None or row.start <= current_end + timedelta(days=1):
                    current.append(idx)
                    current_end = max(current_end or row.end, row.end)
                else:
                    groups.append(current)
                    current = [idx]
                    current_end = row.end
            if current:
                groups.append(current)
        for seq, indices in enumerate(groups, 1):
            part = group.loc[indices]
            start, end = min(part.start), max(part.end)
            if start > AS_OF:
                continue
            president = "Lula III" if label == "Lula" and year >= 2023 else ("Lula I-II" if label == "Lula" else label)
            records.append({
                "president": president, "trip_id": f"{president}-{year}-{seq:03d}",
                "start_date": start.isoformat(), "end_date": end.isoformat(),
                "year": year, "days_abroad": (end - start).days + 1,
                "country_visits": int(part.country.nunique()),
                "countries": "; ".join(sorted(part.country.unique())),
                "source_file": source_file, "source_priority": source_priority,
            })
    return pd.DataFrame(records)


def load_trips() -> pd.DataFrame:
    primary_frames: list[pd.DataFrame] = []
    comparisons: dict[str, pd.DataFrame] = {}
    for label, filename in PRIMARY_FILES.items():
        parsed = parse_wikitext((RAW_TRAVEL / filename).read_text(encoding="utf-8"), filename)
        primary_frames.append(_group_visits(parsed, label, filename, "primary"))
    for label, filename in SECONDARY_FILES.items():
        parsed = parse_wikitext((RAW_TRAVEL / filename).read_text(encoding="utf-8"), filename)
        comparisons[label] = _group_visits(parsed, label, filename, "cross-check")
    trips = pd.concat(primary_frames, ignore_index=True).sort_values(["start_date", "trip_id"])
    trips["parse_conflict"] = ""
    for label, secondary in comparisons.items():
        labels = ["Lula I-II", "Lula III"] if label == "Lula" else [label]
        for president in labels:
            p = trips[trips.president == president].groupby("year").agg(primary_trips=("trip_id", "nunique"), primary_days=("days_abroad", "sum"))
            s = secondary[secondary.president == president].groupby("year").agg(check_trips=("trip_id", "nunique"), check_days=("days_abroad", "sum"))
            comp = p.join(s, how="outer").fillna(0).astype(int)
            for year, row in comp.iterrows():
                if row.primary_trips != row.check_trips or row.primary_days != row.check_days:
                    msg = f"cross-check differs: trips {row.primary_trips}/{row.check_trips}, days {row.primary_days}/{row.check_days} (primary/check)"
                    mask = (trips.president == president) & (trips.year == year)
                    trips.loc[mask, "parse_conflict"] = msg
    return trips.reset_index(drop=True)


def is_international(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes", "sim", "y"}


def load_ipca(path: Path = RAW_RATES / "bcb_sgs_433_ipca_monthly.json") -> pd.Series:
    raw = pd.DataFrame(json.loads(path.read_text(encoding="utf-8-sig")))
    raw["month"] = pd.to_datetime(raw["data"], dayfirst=True).dt.to_period("M")
    raw["rate"] = pd.to_numeric(raw["valor"], errors="coerce") / 100.0
    raw = raw.sort_values("month")
    # Index is 1 in Sep-2026; a payment in month m is multiplied by inflation m+1..Sep-2026.
    factors: dict[pd.Period, float] = {}
    values = raw.set_index("month")["rate"]
    target = pd.Period("2026-09", "M")
    for month in values.index:
        factors[month] = float((1.0 + values[(values.index > month) & (values.index <= target)]).prod())
    return pd.Series(factors, name="ipca_factor_to_2026_09")


def deflate_to_constant(values: Sequence[float] | pd.Series, dates: Sequence[object] | pd.Series,
                        factors: pd.Series) -> pd.Series:
    months = pd.to_datetime(pd.Series(dates), dayfirst=True, errors="coerce").dt.to_period("M")
    mult = months.map(factors)
    return pd.to_numeric(pd.Series(values), errors="coerce") * mult


def _destination_countries(value: object) -> set[str]:
    countries: set[str] = set()
    for segment in re.split(r"[,;]", str(value)):
        tail = segment.rsplit("/", 1)[-1].strip()
        canonical = canonical_country(tail)
        if canonical and canonical not in {"", "Na", "Nan"}:
            countries.add(canonical)
    return countries


def _optional_cpgf(factors: pd.Series) -> pd.DataFrame:
    """Read the optional Presidency card extract without assuming one portal schema.

    Card spending remains a separate series: it is never added to travel-system
    support cost.  Classification is intentionally conservative and auditable.
    """
    path = RAW_TRAVEL / "presidency_cpgf_2013_2026.csv.gz"
    if not path.exists():
        return pd.DataFrame(columns=["president", "year", "cpgf_foreign_records", "cpgf_foreign_total_brl_constant_2026_09"])
    card = pd.read_csv(path, low_memory=False)
    normal = {c: re.sub(r"[^a-z0-9]", "", _ascii(c)) for c in card.columns}
    date_col = next((c for c, n in normal.items() if "data" in n or "date" in n), None)
    value_col = next((c for c, n in normal.items() if any(k in n for k in ("valortransacao", "valor", "amount", "value"))), None)
    if date_col is None or value_col is None:
        raise ValueError("Optional CPGF file must contain a date and transaction-value column")
    card["date"] = pd.to_datetime(card[date_col], dayfirst=True, errors="coerce")
    values = card[value_col].astype(str).str.replace(r"[^0-9,.-]", "", regex=True)
    comma_decimal = values.str.contains(",", regex=False)
    values.loc[comma_decimal] = values.loc[comma_decimal].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    card["value_brl"] = pd.to_numeric(values, errors="coerce")
    text_cols = [c for c in card.columns if card[c].dtype == object and c != value_col]
    text = card[text_cols].fillna("").astype(str).agg(" ".join, axis=1).map(_ascii)
    foreign_terms = sorted(set(COUNTRY_ALIASES) | {"exterior", "internacional", "foreign", "usd", "euro", "dolar"}, key=len, reverse=True)
    pattern = r"\b(?:" + "|".join(re.escape(x) for x in foreign_terms) + r")\b"
    card = card[text.str.contains(pattern, regex=True)]
    card["president"] = card.date.map(lambda x: president_for_date(x) if pd.notna(x) else None)
    card["year"] = card.date.dt.year
    card["constant"] = deflate_to_constant(card.value_brl, card.date, factors).values
    return card.dropna(subset=["president", "year"]).groupby(["president", "year"], as_index=False).agg(
        cpgf_foreign_records=("constant", "size"),
        cpgf_foreign_total_brl_constant_2026_09=("constant", "sum"),
    )


def build_costs(trips: pd.DataFrame) -> pd.DataFrame:
    raw = pd.read_csv(RAW_TRAVEL / "presidency_travel_2014_2026.csv.gz", low_memory=False)
    raw["start_date"] = pd.to_datetime(raw.start, dayfirst=True, errors="coerce")
    raw["end_date"] = pd.to_datetime(raw.end, dayfirst=True, errors="coerce")
    raw = raw[raw.start_date.dt.date <= AS_OF].copy()
    raw["year"] = raw.start_date.dt.year
    raw["president"] = raw.start_date.map(lambda x: president_for_date(x) if pd.notna(x) else None)
    raw["international"] = raw.international.map(is_international)
    raw["spouse_related"] = raw.motive.fillna("").map(_ascii).str.contains(
        r"familiar do sr\.? presidente|primeira dama|conjuge", regex=True
    )
    money = ["per_diem_brl", "tickets_brl", "refund_brl", "other_brl"]
    for col in money:
        raw[col] = pd.to_numeric(raw[col], errors="coerce").fillna(0.0)
    # Portal "Valor devolução" is money returned, so it reduces net cost.
    raw["total_brl"] = raw["per_diem_brl"] + raw["tickets_brl"] + raw["other_brl"] - raw["refund_brl"]
    factors = load_ipca()
    for col in money + ["total_brl"]:
        raw[f"{col}_constant_2026_09"] = deflate_to_constant(raw[col], raw.start_date, factors).values

    trip_windows: list[tuple[pd.Timestamp, pd.Timestamp, set[str], str]] = []
    for _, trip in trips.iterrows():
        trip_windows.append((pd.Timestamp(trip.start_date), pd.Timestamp(trip.end_date), set(str(trip.countries).split("; ")), trip.trip_id))

    def matched_trip(row: pd.Series) -> str | None:
        if not row.international or pd.isna(row.start_date) or pd.isna(row.end_date):
            return None
        destinations = _destination_countries(row.destinations)
        for start, end, countries, trip_id in trip_windows:
            if row.start_date <= end and row.end_date >= start and destinations.intersection(countries):
                return trip_id
        return None

    raw["matched_trip_id"] = raw.apply(matched_trip, axis=1)
    raw["presidential_trip_support"] = raw.matched_trip_id.notna()
    rows: list[dict[str, object]] = []
    for (president, year), group in raw.dropna(subset=["president", "year"]).groupby(["president", "year"]):
        intl = group[group.international]
        support = group[group.presidential_trip_support]
        spouse = group[group.spouse_related & group.international]
        trip_year = trips[(trips.president == president) & (trips.year == year)]
        rec: dict[str, object] = {
            "president": president, "year": int(year), "price_base": "Sep-2026 BRL",
            "records_total": len(group), "records_international": len(intl),
            "records_presidential_trip_support": len(support), "records_spouse_related": len(spouse),
            "trips": int(trip_year.trip_id.nunique()), "days_abroad": int(trip_year.days_abroad.sum()),
        }
        for scope, frame in [("all", group), ("international", intl), ("presidential_support", support), ("spouse_related", spouse)]:
            for col in ["per_diem_brl", "tickets_brl", "refund_brl", "other_brl", "total_brl"]:
                rec[f"{scope}_{col}_constant_2026_09"] = frame[f"{col}_constant_2026_09"].sum(min_count=1)
        support_total = rec["presidential_support_total_brl_constant_2026_09"]
        rec["support_cost_per_trip_constant_2026_09"] = support_total / rec["trips"] if rec["trips"] else np.nan
        rec["support_cost_per_day_constant_2026_09"] = support_total / rec["days_abroad"] if rec["days_abroad"] else np.nan
        rec["coverage_note"] = SUPPORT_LOWER_BOUND_LABEL
        rows.append(rec)
    result = pd.DataFrame(rows)
    cpgf = _optional_cpgf(factors)
    result = result.merge(cpgf, on=["president", "year"], how="outer")
    if "cpgf_foreign_records" not in result:
        result["cpgf_foreign_records"] = np.nan
        result["cpgf_foreign_total_brl_constant_2026_09"] = np.nan
    result["cpgf_coverage_note"] = np.where(
        result["cpgf_foreign_records"].notna(),
        "Conservative text classification of optional Presidency card transactions abroad; separate from travel-system cost",
        "Optional CPGF extract absent or no classified foreign transaction; not included in support cost",
    )
    return result.sort_values(["year", "president"]).reset_index(drop=True)


def _load_monthly_annual(path: Path, name: str) -> pd.DataFrame:
    d = pd.DataFrame(json.loads(path.read_text(encoding="utf-8-sig")))
    d["year"] = pd.to_datetime(d.data, dayfirst=True).dt.year
    d[name] = pd.to_numeric(d.valor, errors="coerce")
    return d.groupby("year", as_index=False)[name].sum(min_count=1)


def _load_funcex() -> pd.DataFrame:
    obj = json.loads((RAW_EXTERNAL / "ipeadata_FUNCEX_XQT.json").read_text(encoding="utf-8-sig"))
    d = pd.DataFrame(obj["value"])
    d["year"] = pd.to_datetime(d.VALDATA, utc=True).dt.year
    d["export_volume_index"] = pd.to_numeric(d.VALVALOR, errors="coerce")
    return d.loc[d.year.between(1995, 2025), ["year", "export_volume_index"]].drop_duplicates("year")


def build_annual(trips: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    years = pd.DataFrame({"year": range(1995, 2026)})
    t = trips[trips.year <= 2025].groupby("year").agg(trips=("trip_id", "nunique"), days=("days_abroad", "sum"), country_visits=("country_visits", "sum")).reset_index()
    annual = years.merge(t, on="year", how="left").fillna({"trips": 0, "days": 0, "country_visits": 0})
    annual = annual.merge(_load_monthly_annual(RAW_EXTERNAL / "bcb_sgs_22885.json", "fdi_usd_million"), on="year", how="left")
    annual = annual.merge(_load_monthly_annual(RAW_EXTERNAL / "bcb_sgs_22708.json", "exports_usd_million"), on="year", how="left")
    annual = annual.merge(_load_funcex(), on="year", how="left")
    ext = pd.read_csv(DATA_DIR / "external_observed.csv")
    ext = ext.pivot(index="year", columns="indicator", values="value").reset_index()
    keep = [c for c in ["year", "fdi_net_inflows_pct_gdp", "commodity_tot_index", "world_gdp_growth_pct", "china_gdp_growth_pct", "us_fed_funds_pct"] if c in ext]
    annual = annual.merge(ext[keep], on="year", how="left")
    back = pd.read_csv(DATA_DIR / "backtest_observed.csv")
    back = back[back.indicator == "brl_per_usd"][["year", "value"]].rename(columns={"value": "brl_per_usd"})
    return annual.merge(back, on="year", how="left")


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    keep = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y2, x2 = y[keep], X[keep]
    beta = np.linalg.lstsq(x2, y2, rcond=None)[0]
    resid = y2 - x2 @ beta
    return beta, resid, keep


def newey_west(y: Sequence[float], X: np.ndarray, max_lag: int = 2) -> tuple[np.ndarray, np.ndarray, int]:
    yv = np.asarray(y, dtype=float)
    beta, resid, keep = _ols(yv, np.asarray(X, dtype=float))
    x = np.asarray(X, dtype=float)[keep]
    n, k = x.shape
    bread = np.linalg.pinv(x.T @ x)
    score = x * resid[:, None]
    meat = score.T @ score
    for lag in range(1, min(max_lag, n - 1) + 1):
        weight = 1.0 - lag / (max_lag + 1.0)
        gamma = score[lag:].T @ score[:-lag]
        meat += weight * (gamma + gamma.T)
    cov = bread @ meat @ bread * n / max(n - k, 1)
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None)), n


def permutation_test(y: Sequence[float], travel: Sequence[float], controls: np.ndarray | None = None,
                     draws: int = 10_000, seed: int = 20261022) -> tuple[float, float]:
    """Freedman-style coefficient test with year-label shuffling, reproducibly."""
    yv, xv = np.asarray(y, float), np.asarray(travel, float)
    z = np.ones((len(yv), 1)) if controls is None else np.asarray(controls, float)
    keep = np.isfinite(yv) & np.isfinite(xv) & np.isfinite(z).all(axis=1)
    yv, xv, z = yv[keep], xv[keep], z[keep]
    mz = np.eye(len(yv)) - z @ np.linalg.pinv(z)
    yr, xr = mz @ yv, mz @ xv
    denom = float(xr @ xr)
    observed = float(xr @ yr / denom) if denom else np.nan
    if not np.isfinite(observed):
        return observed, np.nan
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(draws):
        xp = xv[rng.permutation(len(xv))]
        xpr = mz @ xp
        d = float(xpr @ xpr)
        b = float(xpr @ yr / d) if d else 0.0
        extreme += abs(b) >= abs(observed)
    return observed, (extreme + 1) / (draws + 1)


def aggregate_estimates(annual: pd.DataFrame, draws: int = 10_000) -> pd.DataFrame:
    outcomes = {
        "fdi_usd_million": "US$ million", "fdi_net_inflows_pct_gdp": "% GDP",
        "exports_usd_million": "US$ million", "export_volume_index": "2018=100",
    }
    controls = [c for c in ["commodity_tot_index", "world_gdp_growth_pct", "china_gdp_growth_pct", "brl_per_usd"] if c in annual]
    rows: list[dict[str, object]] = []
    for outcome, units in outcomes.items():
        for measure in ["trips", "days"]:
            for transform in ["level", "first_difference"]:
                for lag in range(3):
                    d = annual[["year", outcome, measure] + controls].copy()
                    d["travel"] = d[measure].shift(lag)
                    if transform == "first_difference":
                        for col in [outcome, "travel"] + controls:
                            d[col] = d[col].diff()
                    d["trend"] = d.year - d.year.min()
                    rhs_controls = controls + (["trend"] if transform == "level" else [])
                    clean = d.dropna(subset=[outcome, "travel"] + rhs_controls)
                    if len(clean) <= len(rhs_controls) + 3:
                        continue
                    X = np.column_stack([np.ones(len(clean)), clean.travel.to_numpy()] + [clean[c].to_numpy() for c in rhs_controls])
                    beta, se, n = newey_west(clean[outcome].to_numpy(), X, max_lag=2)
                    p_controls = X[:, [0] + list(range(2, X.shape[1]))]
                    _, p_perm = permutation_test(clean[outcome], clean.travel, p_controls, draws=draws, seed=20261022 + lag)
                    coef, stderr = float(beta[1]), float(se[1])
                    rows.append({
                        "analysis": "aggregate", "model": transform, "outcome": outcome,
                        "travel_measure": measure, "lag": lag, "coefficient": coef,
                        "std_error": stderr, "ci_low": coef - 1.96 * stderr,
                        "ci_high": coef + 1.96 * stderr, "p_value": 2 * (1 - _normal_cdf(abs(coef / stderr))) if stderr else np.nan,
                        "permutation_p": p_perm, "n": n, "units": units,
                        "controls": "; ".join(rhs_controls),
                        "notes": "Newey-West SE (lag 2); annual 1995-2025 frame; controls reduce usable n",
                    })
    return pd.DataFrame(rows)


def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _cluster_ols(y: np.ndarray, X: np.ndarray, clusters: Sequence[object]) -> tuple[np.ndarray, np.ndarray, int]:
    keep = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y, x, g = y[keep], X[keep], np.asarray(clusters)[keep]
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    groups = pd.unique(g)
    for group in groups:
        score = x[g == group].T @ resid[g == group]
        meat += np.outer(score, score)
    n, k, G = len(y), x.shape[1], len(groups)
    correction = (G / max(G - 1, 1)) * ((n - 1) / max(n - k, 1))
    cov = correction * bread @ meat @ bread
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None)), n


def bilateral_fe_regression(panel: pd.DataFrame, outcome: str = "exports_usd", visit: str = "visit",
                            country: str = "country", year: str = "year", trends: bool = False) -> dict[str, float]:
    """Two-way FE log-export regression, exposed for synthetic validation."""
    d = panel[[country, year, outcome, visit]].dropna().copy()
    d = d[d[outcome] > 0]
    y = np.log(d[outcome].to_numpy(float))
    c_dum = pd.get_dummies(d[country], drop_first=True, dtype=float)
    y_dum = pd.get_dummies(d[year], drop_first=True, dtype=float)
    pieces = [np.ones((len(d), 1)), d[[visit]].to_numpy(float), c_dum.to_numpy(), y_dum.to_numpy()]
    if trends:
        centred = d[year].to_numpy(float) - d[year].mean()
        pieces.append(c_dum.to_numpy() * centred[:, None])
    X = np.column_stack(pieces)
    beta, se, n = _cluster_ols(y, X, d[country].to_numpy())
    return {"coefficient": float(beta[1]), "std_error": float(se[1]), "n": float(n)}


def load_bilateral_panel(trips: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for year in range(1997, 2026):
        obj = json.loads((RAW_EXTERNAL / f"comexstat_exports_by_country_{year}.json").read_text(encoding="utf-8-sig"))
        d = pd.DataFrame(obj["data"]["list"])
        d["year"] = year
        d["country"] = d.country.map(canonical_country)
        d["exports_usd"] = pd.to_numeric(d.metricFOB, errors="coerce")
        frames.append(d[["country", "year", "exports_usd"]])
    panel = pd.concat(frames, ignore_index=True).groupby(["country", "year"], as_index=False).exports_usd.sum()
    visit_rows: list[dict[str, object]] = []
    for _, trip in trips[trips.year.between(1997, 2025)].iterrows():
        for country in str(trip.countries).split("; "):
            visit_rows.append({"country": canonical_country(country), "year": int(trip.year), "visit": 1})
    visits = pd.DataFrame(visit_rows).groupby(["country", "year"], as_index=False).visit.max()
    panel = panel.merge(visits, on=["country", "year"], how="left").fillna({"visit": 0})
    panel = panel.sort_values(["country", "year"])
    for lag in [1, 2]:
        shifted = visits.copy(); shifted["year"] += lag
        shifted = shifted.rename(columns={"visit": f"visit_lag{lag}"})
        panel = panel.merge(shifted, on=["country", "year"], how="left").fillna({f"visit_lag{lag}": 0})
    placebo = visits.copy(); placebo["year"] -= 2
    panel = panel.merge(placebo.rename(columns={"visit": "visit_lead2_placebo"}), on=["country", "year"], how="left").fillna({"visit_lead2_placebo": 0})
    return panel


def bilateral_estimates(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for trends in [False, True]:
        for variable, lag in [("visit", 0), ("visit_lag1", 1), ("visit_lag2", 2), ("visit_lead2_placebo", -2)]:
            result = bilateral_fe_regression(panel, visit=variable, trends=trends)
            b, se = result["coefficient"], result["std_error"]
            low, high = b - 1.96 * se, b + 1.96 * se
            rows.append({
                "analysis": "bilateral", "model": "country+year FE+country trends" if trends else "country+year FE",
                "outcome": "log_exports_usd", "travel_measure": "visit_placebo_t_plus_2" if lag == -2 else "visit",
                "lag": lag, "coefficient": 100 * math.expm1(b),
                "std_error": 100 * se, "ci_low": 100 * math.expm1(low), "ci_high": 100 * math.expm1(high),
                "p_value": 2 * (1 - _normal_cdf(abs(b / se))) if se else np.nan,
                "permutation_p": np.nan, "n": int(result["n"]), "units": "% change in exports",
                "controls": "country FE; year FE" + ("; country-specific linear trends" if trends else ""),
                "notes": "Clustered SE by partner; positive-export country-years; each visit timing estimated separately",
            })
    return pd.DataFrame(rows)


def _fmt(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "missing"
    return f"{float(value):,.{digits}f}"


def _summaries(trips: pd.DataFrame, costs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    trip_summary = trips.groupby("president", sort=False).agg(trips=("trip_id", "nunique"), country_visits=("country_visits", "sum"), days=("days_abroad", "sum")).reset_index()
    order = {name: i for i, (name, _, _) in enumerate(PRESIDENTS)}
    trip_summary["order"] = trip_summary.president.map(order)
    trip_summary = trip_summary.sort_values("order").drop(columns="order")
    cost_summary = costs.groupby("president", sort=False).agg(
        support_cost=("presidential_support_total_brl_constant_2026_09", lambda x: x.sum(min_count=1)),
        international_cost=("international_total_brl_constant_2026_09", lambda x: x.sum(min_count=1)),
        all_cost=("all_total_brl_constant_2026_09", lambda x: x.sum(min_count=1)),
        spouse_related=("spouse_related_total_brl_constant_2026_09", lambda x: x.sum(min_count=1)),
        cpgf_foreign=("cpgf_foreign_total_brl_constant_2026_09", lambda x: x.sum(min_count=1)),
    ).reset_index()
    cost_summary = trip_summary[["president"]].merge(cost_summary, on="president", how="left")
    return trip_summary, cost_summary


def _cited_figures() -> pd.DataFrame:
    return pd.read_csv(RAW_TRAVEL / "cited_figures_press.csv")


def _press_cost_context(year: int, cited: pd.DataFrame) -> str:
    notes: list[str] = []
    annual = cited[cited.item.eq("international_trip_cost_2025")]
    if year == 2025 and not annual.empty:
        r = annual.iloc[0]
        notes.append(f"R$ {_fmt(r.value)}m (2025 international-trip press estimate; {r.basis})")
    period = cited[cited.item.eq("presidency_travel_spending_2023_2025")]
    if 2023 <= year <= 2025 and not period.empty:
        r = period.iloc[0]
        notes.append(f"R$ {_fmt(r.value)}m total for 2023–2025 (not allocable by year; {r.basis})")
    return "; ".join(notes) or "—"


def write_reports(trips: pd.DataFrame, costs: pd.DataFrame, estimates: pd.DataFrame) -> None:
    ts, cs = _summaries(trips, costs)
    cited = _cited_figures()
    bilateral = estimates[estimates.analysis == "bilateral"]
    agg = estimates[(estimates.analysis == "aggregate") & (estimates.lag == 0)]
    trip_lines = [
        f"| {r.president} | {r.trips} | {r.country_visits} | {r.days} | {COUNT_CONTEXT.get(r.president, '—')} |"
        for r in ts.itertuples()
    ]
    cost_lines = [f"| {r.president} | {_fmt(r.support_cost/1e6)} | {_fmt(r.international_cost/1e6)} | {_fmt(r.all_cost/1e6)} | {_fmt(r.spouse_related/1e6)} | {_fmt(r.cpgf_foreign/1e6)} |" for r in cs.itertuples()]
    yearly_cost_lines = [
        f"| {int(r.year)} | {r.president} | {_fmt(r.presidential_support_total_brl_constant_2026_09/1e6)} | "
        f"{_fmt(r.international_total_brl_constant_2026_09/1e6)} | "
        f"{_fmt(r.cpgf_foreign_total_brl_constant_2026_09/1e6)} | {_press_cost_context(int(r.year), cited)} |"
        for r in costs.sort_values("year").itertuples()
    ]
    bil_lines = [f"| {r.model} | {r.travel_measure} | {r.lag} | {_fmt(r.coefficient,2)}% | [{_fmt(r.ci_low,2)}%, {_fmt(r.ci_high,2)}%] | {_fmt(r.p_value,3)} | {r.n} |" for r in bilateral.itertuples()]
    agg_lines = [f"| {r.model} | {r.outcome} | {r.travel_measure} | {_fmt(r.coefficient,3)} | [{_fmt(r.ci_low,3)}, {_fmt(r.ci_high,3)}] | {_fmt(r.permutation_p,3)} | {r.n} |" for r in agg.itertuples()]
    conflict_years = trips.loc[trips.parse_conflict.ne(""), ["president", "year", "parse_conflict"]].drop_duplicates()
    conflicts = "\n".join(f"- {r.president}, {r.year}: {r.parse_conflict}." for r in conflict_years.itertuples()) or "- No primary/cross-check count differences detected."
    report = f"""# Presidential international travel, costs, FDI and exports

Generated from the repository's frozen local sources. Results are descriptive associations, not causal effects or forecasts.

> **Bottom line:** The data show **no robust evidence that presidential visits raise exports to the visited country**. Visits tend to go to partners whose trade is already growing. The t+2 placebo is about as large and statistically significant as the t−1 estimate, and no visit coefficient is distinguishable from zero after adding country-specific trends.

## Counts cross-check

| President | Wikipedia-derived trips | Country-visits | Listed days abroad (lower bound) | Cited press/page-lead context |
|---|---:|---:|---:|---|
{chr(10).join(trip_lines)}

Trips are consistently reconstructed departure-return itineraries; rows sharing an explicit trip number (or overlapping/directly contiguous dates where no number exists) are one trip. Days are a **lower bound**: they are the inclusive span of listed stop dates and can exclude outbound/return travel days. The cited counts use different list versions, completeness, counting rules and cut-off dates. Page leads can count visits or announced trips differently from the archived table, while this build groups multi-country stops into one itinerary. FHC's press figure comes from `cited_figures_press.csv`; the Lula III and Bolsonaro lead/table discrepancies are visible in the frozen Wikipedia snapshots.

## {SUPPORT_LOWER_BOUND_LABEL}

Constant September-2026 R$ million.

| President | Matched presidential-trip support — LOWER BOUND | All Presidency international travel-system records (context) | All Presidency-scope records | Spouse-related support | Foreign CPGF (separate) |
|---|---:|---:|---:|---:|---:|
{chr(10).join(cost_lines)}

The first column is only a lower bound: an international record must overlap a listed presidential trip and match a destination country. “All international” and “all Presidency-scope” are context, not amounts attributed to the president. Spouse-related means support/security records whose motive explicitly mentions family, first lady, or spouse. The travel-system extract excludes Air Force aircraft, payment-card hotel/expense items, and unitemised costs of the President and spouse. No cost estimate is made before 2014.

### Yearly cost context

| Year | President | Matched support LOWER BOUND, R$ m constant Sep-2026 | All Presidency international records, R$ m constant Sep-2026 (context) | Foreign CPGF, R$ m constant Sep-2026 (separate) | Cited press estimate (context; source basis) |
|---:|---|---:|---:|---:|---|
{chr(10).join(yearly_cost_lines)}

Press figures retain their stated source basis and are not combined with or silently compared as like-for-like with constant-price travel-system records. If `presidency_cpgf_2013_2026.csv.gz` exists, conservatively identified foreign card transactions appear as the separate CPGF series above; they are never merged into the matched-support lower bound.

## Bilateral export estimates (primary)

Country and year fixed effects; standard errors clustered by partner. Coefficients are transformed to percent changes in exports.

| Model | Timing | Lag | Estimate | 95% CI | p-value | n |
|---|---|---:|---:|---:|---:|---:|
{chr(10).join(bil_lines)}

The fixed-effects model estimates +11.33% at t−1 (p=0.026), but the t+2 placebo—a future visit assigned to the current year—is nearly as large at +10.05% (p=0.046). That failed placebo says the apparent lead/lag pattern is consistent with presidents selecting partners whose exports were already growing. With country-specific trends, every interval crosses zero. **Plain reading: there is no robust evidence here that presidential visits raise exports to the visited country.**

## Aggregate annual estimates (contemporaneous levels and first differences)

Annual frame is 1995-2025 (31 years before missing controls/lags). Newey-West standard errors use lag 2; permutation p-values use 10,000 year shuffles and seed 20261022. The complete level/difference and lag 0-2 grid is in the estimates CSV.

| Model | Outcome | Travel measure | Estimate | 95% CI | permutation p | n |
|---|---|---|---:|---:|---:|---:|
{chr(10).join(agg_lines)}

The annual frame has only n=31 before missing controls reduce the displayed contemporaneous specifications to n=25 in levels and n=24 in first differences. FDI coefficients are indistinguishable from zero in both levels and changes. Exports per trip are positive in levels (US$3,472.624m; permutation p=0.001), but do **not** survive first differences (US$1,049.290m; 95% CI −75.850 to 2,174.430; permutation p=0.333). Export volume has the same pattern. **Plain reading: aggregate FDI/export regressions are dominated by global cycles; the exports-per-trip levels result is a common-trend artefact, not robust evidence of a travel effect.**

## Data gaps and cross-checks

- Cost microdata begin in 2014; pre-2014 cost cells are explicitly missing, not zero.
- 2026 is partial through the latest dates in the frozen inputs. Outcome regressions stop at 2025.
- Wikipedia trip lists are editable secondary sources. Portuguese is primary for FHC/Lula and English for Dilma/Temer/Bolsonaro, as fixed in the task.
- FHC has no supplied English cross-check file.
- CPGF data are optional. When absent, the separate card series is missing; press card figures remain labelled context and are never added to computed costs.
- ComexStat contains positive recorded export destinations; bilateral regressions do not turn absent country-years into invented zero trade.

{conflicts}

See `docs/presidential_travel.md` for all assumptions and formulas, and the self-contained HTML tool for yearly detail.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")

    method = """# Method: presidential travel, costs and external outcomes

## Scope and invariants

The build is offline and deterministic. It uses only frozen repository inputs, treats every president identically, retains value-year pairs, and never interpolates a missing observation. Presidential labels are FHC (1995-2002), Lula I-II (2003-2010), Dilma Rousseff (to 30 August 2016), Michel Temer (from 31 August 2016), Jair Bolsonaro (2019-2022), and Lula III (2023-2026).

## Trips and days

Year-specific wikitext tables are parsed. Country cells come from flag templates; dates accept English and Portuguese month names and same- or cross-month ranges. Primary sources are Portuguese for FHC and Lula and English for the other presidents. A table's explicit trip number groups multi-country legs. Where a source has no trip number, rows whose date intervals overlap or are directly contiguous are grouped as one departure-return itinerary. A trip's day count is the inclusive union span from earliest start through latest end; country-visits are unique countries in that trip. Primary/cross-check differences are retained as flags rather than silently reconciled.

This grouping assumes a shared explicit number or overlapping/directly contiguous listed dates identifies one continuous itinerary. It can undercount separately ticketed trips on the same or consecutive days or overstate days if a source omits an intervening return to Brazil. Listed days are explicitly a lower bound because stop dates can exclude outbound and return travel days. Press/page-lead counts are context only: differences can arise from list completeness, trip-versus-stop counting, travel-day rules and snapshot cut-off dates. The original rows remain recoverable from the cited raw files.

## Costs and prices

For each Portal record, nominal net cost is `per diem + tickets + other - refund`; the source field is Portal “Valor devolução” (money returned). Each component is multiplied by cumulative monthly IPCA after its start month through September 2026. Thus September 2026 has factor 1; dates without a price factor remain missing.

A presidential-trip support record must (1) be flagged international, (2) overlap a listed trip date interval, and (3) have at least one destination country matching that trip. Matching normalises Portuguese/English country names and common three-letter flag codes. Other Presidency international travel is reported separately. Spouse-related records use the pre-fixed motive terms “FAMILIAR DO SR PRESIDENTE”, “PRIMEIRA-DAMA”, or “CONJUGE”; these are staff/security support costs, not an itemised spouse bill.

Every matched-support amount is labelled a **lower bound**. The travel system covers Presidency bodies, selected Defence support, and other organs citing presidential missions. It excludes Air Force aircraft, payment-card hotel/expense items, and unitemised costs of the President and spouse. Optional `presidency_cpgf_2013_2026.csv.gz` is a separate card series: conservatively identified foreign transactions are reported separately and never mixed into travel-system costs. Published figures in `cited_figures_press.csv` are context only and retain their source basis.

## Aggregate association

The annual 1995-2025 frame contains trips, days, monthly BCB FDI and goods exports summed to annual values, WDI FDI as percent of GDP from the existing observed-data build, and the annual FUNCEX export quantum index. For each outcome, travel measure, lag 0-2 and transformation:

`y_t = a + b travel_(t-lag) + controls_t + trend + error_t`

Level models contain a linear trend; first-difference models difference outcomes, travel and controls and omit the trend. Controls are the local commodity terms-of-trade index, world GDP growth, China GDP growth, and BRL/USD. Coefficient intervals use Newey-West covariance with lag 2. A two-sided permutation p-value shuffles travel year labels 10,000 times after partialling the other regressors (seed 20261022 plus lag). Missing controls are listwise deleted and n is reported per model. These low-powered time-series associations begin with only 31 years and are vulnerable to global cycles, simultaneity and destination selection. A levels coefficient is not treated as robust unless it survives first differences; the exports-per-trip result does not.

## Bilateral association

The 1997-2025 panel uses log positive FOB exports to each ComexStat partner. Separate models estimate visits at t, t-1 and t-2:

`log(exports_ct) = country FE + year FE + b visit_c,t-lag + error_ct`

Standard errors are clustered by country. Robustness adds country-specific linear trends. The placebo moves actual visits two years earlier, so a visit at t+2 predicts exports at t. Log coefficients and confidence bounds are reported as `100*(exp(b)-1)`. Each timing is estimated separately. The placebo is about as large and significant as t−1, while no coefficient survives country trends; this supports the reading that visits tend to follow already-growing trade partners, not a causal export effect.

## Reproducibility and output interpretation

Run `python -m src.presidential_travel`. The CSVs are machine-readable sources for the report and embedded HTML. Empty/missing means unavailable, never zero, except visit indicators and annual trip counts in a known covered list where no listed trip is zero. The HTML contains inline CSS, JavaScript, SVG and embedded JSON and makes no request.
"""
    METHOD_OUT.write_text(method, encoding="utf-8")


def write_html(trips: pd.DataFrame, costs: pd.DataFrame, estimates: pd.DataFrame, annual: pd.DataFrame) -> None:
    ts, cs = _summaries(trips, costs)
    cited = _cited_figures()
    trip_years = trips.groupby(["president", "year"]).agg(trips=("trip_id", "nunique"), days_abroad=("days_abroad", "sum"), country_visits=("country_visits", "sum")).reset_index()
    yearly = annual.merge(trip_years, on="year", how="outer", suffixes=("_all", ""))
    cost_columns = [
        "president", "year", "presidential_support_total_brl_constant_2026_09",
        "international_total_brl_constant_2026_09", "cpgf_foreign_total_brl_constant_2026_09",
    ]
    yearly = yearly.merge(costs[cost_columns], on=["president", "year"], how="outer").sort_values(["year", "president"])
    yearly["press_cost_context"] = yearly.year.map(lambda y: _press_cost_context(int(y), cited))
    payload = {
        "yearly": json.loads(yearly.replace({np.nan: None}).to_json(orient="records")),
        "trips": json.loads(trips.replace({np.nan: None}).to_json(orient="records")),
        "summary": json.loads(ts.merge(cs, on="president", how="left").replace({np.nan: None}).to_json(orient="records")),
        "estimates": json.loads(estimates.replace({np.nan: None}).to_json(orient="records")),
        "count_context": COUNT_CONTEXT,
    }
    embedded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brazil presidential travel, costs and trade</title>
<style>
:root{{--bg:#f7f7f4;--panel:#fff;--text:#182127;--muted:#59666d;--line:#d7dddf;--accent:#39759b;--gap:#9aa3a8;--shadow:0 6px 24px #17212b12;color-scheme:light dark}}
@media(prefers-color-scheme:dark){{:root{{--bg:#101619;--panel:#182126;--text:#eef4f6;--muted:#aebbc1;--line:#35434a;--accent:#78b7da;--gap:#66737a;--shadow:none}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}} main{{max-width:1180px;margin:auto;padding:28px 18px 60px}} h1{{font-size:clamp(1.8rem,4vw,3.2rem);line-height:1.05;margin:.2em 0}} h2{{margin-top:2rem}} .lede{{color:var(--muted);max-width:850px;font-size:1.05rem}} .toolbar,.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}} .toolbar{{padding:14px;margin:24px 0;display:flex;gap:12px;align-items:center;flex-wrap:wrap;position:sticky;top:8px;z-index:2}} select{{font:inherit;padding:8px 34px 8px 10px;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:7px}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:15px}} .card{{padding:16px;overflow:auto}} .finding{{border-left:6px solid var(--accent);font-size:1.06rem;margin:18px 0;padding:18px 20px}} .metric{{font-size:1.8rem;font-weight:700}} .small,.note{{color:var(--muted);font-size:.88rem}} svg{{width:100%;height:260px;display:block}} .axis{{stroke:var(--line)}} .label{{fill:var(--muted);font-size:11px}} .tip{{fill:var(--text);font-size:11px}} table{{border-collapse:collapse;width:100%;min-width:680px}} th,td{{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}} th:first-child,td:first-child{{text-align:left}} th{{position:sticky;top:0;background:var(--panel)}} .gap{{background:repeating-linear-gradient(135deg,transparent,transparent 6px,var(--line) 6px,var(--line) 8px);color:var(--muted)}} .pill{{display:inline-block;padding:2px 8px;border:1px solid var(--line);border-radius:99px;margin:2px}} details{{margin:.7rem 0}} a{{color:var(--accent)}}
</style></head><body><main>
<p class="small">OFFLINE ANALYTICAL TOOL · DATA THROUGH FROZEN 2026 INPUTS</p><h1>Presidential travel, costs and external outcomes</h1>
<p class="lede">A neutral comparison of listed international trips from FHC through Lula III. Every matched-support cost is a lower bound, not a complete trip bill.</p>
<div class="card finding"><strong>Bottom line:</strong> The data show <strong>no robust evidence that presidential visits raise exports to the visited country</strong>. The t+2 placebo is about as large and significant as t−1, and no visit coefficient is distinguishable from zero with country-specific trends. Visits tend to go to partners whose trade is already growing.</div>
<div class="toolbar"><label for="president">President</label><select id="president"></select><span id="coverage" class="small"></span></div>
<section class="grid" id="metrics"></section>
<h2>Year by year</h2><div class="grid"><div class="card"><h3>Trips and listed days abroad (days are a lower bound)</h3><svg id="travelChart" role="img" aria-label="Yearly trips and lower-bound listed days abroad"></svg></div><div class="card"><h3>{html.escape(SUPPORT_LOWER_BOUND_LABEL)}</h3><svg id="costChart" role="img" aria-label="Yearly lower-bound support cost in constant September 2026 reais"></svg><p class="note">Hatched years mean no cost microdata before 2014. A zero-height bar after 2014 means no matched record, not zero total mission cost.</p></div></div>
<div class="card" style="margin-top:15px"><h3>FDI and goods exports</h3><svg id="externalChart" role="img" aria-label="Annual FDI and exports"></svg><p class="note">US$ million, BCB monthly flows summed by year. Shared national series; the selector only highlights the selected presidency years.</p></div>
<h2>Counts cross-check</h2><div class="card"><table id="summaryTable"><thead><tr><th>President</th><th>Wikipedia-derived trips</th><th>Country-visits</th><th>Listed days (lower bound)</th><th>Cited press/page-lead context</th><th>Matched support LOWER BOUND, R$ m</th><th>All Presidency international records, R$ m (context)</th></tr></thead><tbody></tbody></table><p class="note">Differences reflect list completeness, counting rules, stop-date day counts that can exclude travel days, and cut-off dates. Multi-country stops are grouped into one itinerary here.</p></div>
<h2>Yearly cost context</h2><div class="card"><table id="costContextTable"><thead><tr><th>Year</th><th>President</th><th>Matched support LOWER BOUND, R$ m constant Sep-2026</th><th>All Presidency international records, R$ m constant Sep-2026 (context)</th><th>Foreign CPGF, R$ m constant Sep-2026 (separate)</th><th>Cited press estimate (context; source basis)</th></tr></thead><tbody></tbody></table><p class="note">Press figures retain their cited basis and are never merged into computed costs. If the optional CPGF extract exists, identifiable foreign card transactions appear only in the separate card column.</p></div>
<h2>Regression results</h2><div class="grid"><div class="card"><h3>Bilateral export panel (primary)</h3><div id="bilateral"></div><p><strong>Reading:</strong> t−1 is +11.33% (p=.026), but the future-visit placebo is nearly as large at +10.05% (p=.046). With country trends every interval crosses zero. This is consistent with visits going to already-growing partners, not a robust visit effect.</p></div><div class="card"><h3>Aggregate annual models</h3><div id="aggregate"></div><p><strong>Reading:</strong> The frame has only n=31 before missing controls. FDI has no distinguishable relationship. Exports per trip is positive in levels, but does not survive first differences (permutation p=.333), so it is a common-trend artefact. Global cycles dominate these aggregate regressions.</p></div></div>
<h2>Data gaps and assumptions</h2><div class="card"><ul><li>No cost microdata before 2014; no values are backfilled.</li><li>Air Force aircraft, payment-card hotel/expense items, and unitemised costs of the President and spouse are excluded from the matched-support lower bound.</li><li>“Spouse-related” identifies support/security motives, not the spouse's personal bill.</li><li>CPGF is optional and always separate. Press totals are context only and never combined with computed costs.</li><li>2026 is partial; outcome regressions end in 2025.</li><li>Portuguese lists are primary for FHC/Lula; English lists for Dilma/Temer/Bolsonaro. Cross-check disagreements remain visible in trip data.</li><li>Annual n starts at 31 but missing controls and lags reduce each regression's n.</li><li>Bilateral visits are selected, not random. Fixed effects do not make the estimates causal.</li></ul><details><summary>Definitions</summary><p>Trip = one reconstructed departure-return itinerary. Listed days are an inclusive stop-date span and a lower bound because travel days can be absent. Country-visits count distinct destinations per trip. A matched support cost must be an international Portal record overlapping the trip and matching a destination. Constant prices cumulate monthly IPCA through September 2026.</p></details></div>
<script>const DATA={embedded};
const COLORS=['#4e79a7','#59a14f','#f28e2b','#b07aa1','#76b7b2','#e15759']; const names=DATA.summary.map(d=>d.president); const color=n=>COLORS[names.indexOf(n)%COLORS.length]; const fmt=(v,d=0)=>v==null?'missing':Number(v).toLocaleString(undefined,{{maximumFractionDigits:d,minimumFractionDigits:d}}); const mil=v=>v==null?null:v/1e6;
const sel=document.querySelector('#president'); names.forEach(n=>sel.add(new Option(n,n))); sel.value=names.at(-1); sel.onchange=render;
function svgBars(id, rows, key, overlay, money=false){{const el=document.querySelector(id),W=560,H=250,m={{l:44,r:42,t:18,b:34}},years=rows.map(d=>d.year), vals=rows.map(d=>d[key]).filter(v=>v!=null), ovs=overlay?rows.map(d=>d[overlay]).filter(v=>v!=null):[]; const max=Math.max(...vals,...ovs,1), x=i=>m.l+i*(W-m.l-m.r)/rows.length, bw=Math.max(2,(W-m.l-m.r)/rows.length-3), y=v=>H-m.b-(v/max)*(H-m.t-m.b); let s=`<line class="axis" x1="${{m.l}}" y1="${{H-m.b}}" x2="${{W-m.r}}" y2="${{H-m.b}}"/>`;
rows.forEach((d,i)=>{{if(d[key]==null) s+=`<rect class="gap" x="${{x(i)}}" y="${{m.t}}" width="${{bw}}" height="${{H-m.t-m.b}}"><title>${{d.year}}: no cost data</title></rect>`; else s+=`<rect x="${{x(i)}}" y="${{y(d[key])}}" width="${{bw}}" height="${{H-m.b-y(d[key])}}" fill="${{color(d.president)}}"><title>${{d.year}}: ${{fmt(money?d[key]/1e6:d[key],1)}}${{money?'m constant R$':''}}</title></rect>`; if(i%2===0)s+=`<text class="label" x="${{x(i)}}" y="${{H-10}}">${{String(d.year).slice(2)}}</text>`}});
if(overlay){{s+=`<polyline fill="none" stroke="var(--accent)" stroke-width="2" points="${{rows.map((d,i)=>`${{x(i)+bw/2}},${{y(d[overlay]||0)}}`).join(' ')}}"/>`;}} s+=`<text class="label" x="4" y="${{m.t+8}}">${{money?fmt(max/1e6,1)+'m':fmt(max)}}</text>`; el.setAttribute('viewBox',`0 0 ${{W}} ${{H}}`);el.innerHTML=s;}}
function render(){{const p=sel.value, s=DATA.summary.find(d=>d.president===p), rows=DATA.yearly.filter(d=>d.president===p).sort((a,b)=>a.year-b.year); document.querySelector('#coverage').textContent=rows.length?`${{rows[0].year}}–${{rows.at(-1).year}}`:''; const cost=s.support_cost==null?'No cost data':`R$ ${{fmt(mil(s.support_cost),1)}}m`; document.querySelector('#metrics').innerHTML=`<div class="card"><div class="small">Trips</div><div class="metric">${{fmt(s.trips)}}</div></div><div class="card"><div class="small">Listed days abroad — LOWER BOUND</div><div class="metric">${{fmt(s.days)}}</div></div><div class="card"><div class="small">Matched support cost — LOWER BOUND</div><div class="metric">${{cost}}</div><div class="small">travel-system records only; constant Sep-2026; covered years</div></div>`; svgBars('#travelChart',rows,'trips','days_abroad'); svgBars('#costChart',rows,'presidential_support_total_brl_constant_2026_09',null,true); const ext=DATA.yearly.filter((d,i,a)=>a.findIndex(x=>x.year===d.year)===i); svgBars('#externalChart',ext,'exports_usd_million','fdi_usd_million'); document.querySelectorAll('#summaryTable tbody tr').forEach(tr=>tr.style.outline=tr.dataset.p===p?'2px solid var(--accent)':'none');}}
document.querySelector('#summaryTable tbody').innerHTML=DATA.summary.map(s=>`<tr data-p="${{s.president}}"><td><span class="pill" style="border-color:${{color(s.president)}}">${{s.president}}</span></td><td>${{fmt(s.trips)}}</td><td>${{fmt(s.country_visits)}}</td><td>${{fmt(s.days)}}</td><td>${{DATA.count_context[s.president]||'—'}}</td><td>${{fmt(mil(s.support_cost),1)}}</td><td>${{fmt(mil(s.international_cost),1)}}</td></tr>`).join('');
const costRows=DATA.yearly.filter(d=>d.year>=2014&&d.president); document.querySelector('#costContextTable tbody').innerHTML=costRows.map(d=>`<tr><td>${{d.year}}</td><td>${{d.president}}</td><td>${{fmt(mil(d.presidential_support_total_brl_constant_2026_09),1)}}</td><td>${{fmt(mil(d.international_total_brl_constant_2026_09),1)}}</td><td>${{fmt(mil(d.cpgf_foreign_total_brl_constant_2026_09),1)}}</td><td>${{d.press_cost_context}}</td></tr>`).join('');
const bil=DATA.estimates.filter(d=>d.analysis==='bilateral'); document.querySelector('#bilateral').innerHTML=bil.map(d=>`<p><b>${{d.model.replace('country+year FE','FE')}} · ${{d.lag===-2?'Placebo t+2':'Visit lag '+d.lag}}</b>: ${{fmt(d.coefficient,2)}}% <span class="small">95% CI ${{fmt(d.ci_low,2)}} to ${{fmt(d.ci_high,2)}}; p=${{fmt(d.p_value,3)}}; n=${{d.n}}</span></p>`).join('');
const agg=DATA.estimates.filter(d=>d.analysis==='aggregate'&&d.lag===0); document.querySelector('#aggregate').innerHTML=agg.map(d=>`<p><b>${{d.model}} · ${{d.outcome}} on ${{d.travel_measure}}</b>: ${{fmt(d.coefficient,3)}} <span class="small">CI ${{fmt(d.ci_low,3)}} to ${{fmt(d.ci_high,3)}}; perm p=${{fmt(d.permutation_p,3)}}; n=${{d.n}}</span></p>`).join(''); render();
</script></main></body></html>'''
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(page, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permutations", type=int, default=10_000, help="draws per aggregate permutation test")
    args = parser.parse_args(argv)
    trips = load_trips()
    costs = build_costs(trips)
    annual = build_annual(trips, costs)
    aggregate = aggregate_estimates(annual, draws=args.permutations)
    bilateral = bilateral_estimates(load_bilateral_panel(trips))
    estimates = pd.concat([aggregate, bilateral], ignore_index=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    trips.to_csv(TRIPS_OUT, index=False)
    costs.to_csv(COSTS_OUT, index=False)
    estimates.to_csv(ESTIMATES_OUT, index=False)
    write_reports(trips, costs, estimates)
    write_html(trips, costs, estimates, annual)
    print(f"wrote {len(trips)} trips, {len(costs)} cost rows, {len(estimates)} estimates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
