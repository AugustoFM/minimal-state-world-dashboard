"""Federal SOE inventory, privatisation cash-flow paths, and PZ report.

The module reads only archived inputs.  Running ``python -m src.privatisation``
rebuilds the two processed CSV files and both Markdown outputs owned by PZ.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd
import yaml
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/soe"
INVENTORY_PATH = ROOT / "data/brazil/soe_inventory.csv"
DIVIDENDS_PATH = ROOT / "data/brazil/soe_dividends.csv"
REPORT_PATH = ROOT / "outputs/privatisation.md"
DOC_PATH = ROOT / "docs/privatisation.md"
SALE_YEARS = (2027, 2028, 2029, 2030)
PACKAGES = ("f5", "broad", "broad_bb_petrobras")
P_TO_B_RANGE = (0.5, 1.5)
DISCOUNT_RANGE = (0.0, 0.15)
TIER_B_COMPLETION_RANGE = (0.3, 0.8)
POSTALIS_RANGE_BRL_MILLION = (0.0, 7_799.19)
PETROBRAS_STATE_STAKE_PCT = 36.61
PETROBRAS_INDIRECT_STAKE_PCT = 7.94
PETROBRAS_UNION_DIRECT_STAKE_PCT = (
    PETROBRAS_STATE_STAKE_PCT - PETROBRAS_INDIRECT_STAKE_PCT
)
PETROBRAS_DIVIDEND_SCALE = (
    PETROBRAS_STATE_STAKE_PCT / PETROBRAS_UNION_DIRECT_STAKE_PCT
)


@dataclass(frozen=True)
class Company:
    name: str
    short: str
    group: str
    page: int
    dependent: bool = False


# Page numbers are printed RAEEF pages.  This is the bulletin's complete list
# of directly controlled companies; subsidiaries are deliberately excluded.
COMPANIES = (
    Company("Agencia Brasileira Gestora de Fundos Garantidores e Garantias S.A.", "ABGF", "financial", 42),
    Company("Amazonia Azul Tecnologias de Defesa S.A.", "AMAZUL", "energy/defence", 44, True),
    Company("Autoridade Portuaria de Santos", "SPA", "infrastructure", 46),
    Company("Banco da Amazonia S.A.", "BASA", "financial", 48),
    Company("Banco do Brasil S.A.", "BB", "financial", 50),
    Company("Banco do Nordeste do Brasil S.A.", "BNB", "financial", 52),
    Company("Banco Nacional de Desenvolvimento Economico e Social", "BNDES", "financial", 54),
    Company("Caixa Economica Federal", "CAIXA", "financial", 56),
    Company("Casa da Moeda do Brasil", "CMB", "industry", 58),
    Company("Centrais de Abastecimento de Minas Gerais S.A.", "CEASAMINAS", "food supply", 60),
    Company("Centrais Eletricas Brasileiras S.A.", "ELETROBRAS", "energy", 62),
    Company("Companhia Brasileira de Trens Urbanos", "CBTU", "infrastructure", 64, True),
    Company("Companhia de Desenvolvimento dos Vales do Sao Francisco e do Parnaiba", "CODEVASF", "infrastructure", 66, True),
    Company("Companhia de Entrepostos e Armazens Gerais de Sao Paulo", "CEAGESP", "food supply", 68),
    Company("Companhia de Pesquisa de Recursos Minerais", "CPRM", "research", 70, True),
    Company("Companhia Docas do Ceara", "CDC", "infrastructure", 72),
    Company("Companhia Docas do Espirito Santo", "CODESA", "infrastructure", 74),
    Company("Companhia das Docas do Estado da Bahia", "CODEBA", "infrastructure", 76),
    Company("Companhia Docas do Rio Grande do Norte", "CODERN", "infrastructure", 78),
    Company("Companhia Docas do Para", "CDP", "infrastructure", 80),
    Company("Companhia Docas do Rio de Janeiro", "CDRJ", "infrastructure", 82),
    Company("Companhia Nacional de Abastecimento", "CONAB", "food supply", 84, True),
    Company("Empresa Brasil de Comunicacao S.A.", "EBC", "technology", 86, True),
    Company("Empresa Brasileira de Administracao de Petroleo e Gas Natural", "PPSA", "energy", 88),
    Company("Empresa Brasileira de Correios e Telegrafos", "CORREIOS", "services", 90),
    Company("Empresa Brasileira de Hemoderivados e Biotecnologia", "HEMOBRAS", "industry", 92),
    Company("Empresa Brasileira de Infraestrutura Aeroportuaria", "INFRAERO", "infrastructure", 94),
    Company("Empresa Brasileira de Pesquisa Agropecuaria", "EMBRAPA", "research", 96, True),
    Company("Empresa Brasileira de Servicos Hospitalares", "EBSERH", "health", 98, True),
    Company("Empresa de Pesquisa Energetica", "EPE", "research", 100, True),
    Company("Empresa de Planejamento e Logistica S.A.", "EPL", "infrastructure", 102, True),
    Company("Empresa de Tecnologia e Informacoes da Previdencia", "DATAPREV", "technology", 104),
    Company("Empresa de Trens Urbanos de Porto Alegre S.A.", "TRENSURB", "infrastructure", 106, True),
    Company("Empresa Gerencial de Projetos Navais", "EMGEPRON", "defence", 108),
    Company("Empresa Gestora de Ativos S.A.", "EMGEA", "financial", 110),
    Company("Engenharia, Construcoes e Ferrovias S.A.", "VALEC", "infrastructure", 112, True),
    Company("Financiadora de Estudos e Projetos", "FINEP", "financial", 114),
    Company("Hospital de Clinicas de Porto Alegre", "HCPA", "health", 116, True),
    Company("Hospital Nossa Senhora da Conceicao S.A.", "GHC", "health", 118, True),
    Company("Industria de Material Belico do Brasil", "IMBEL", "defence", 120, True),
    Company("Industrias Nucleares do Brasil S.A.", "INB", "energy/defence", 122, True),
    Company("NAV Brasil Servicos de Navegacao Aerea S.A.", "NAV BRASIL", "infrastructure", 124),
    Company("Nuclebras Equipamentos Pesados S.A.", "NUCLEP", "energy/defence", 126, True),
    Company("Petroleo Brasileiro S.A.", "PETROBRAS", "energy", 128),
    Company("Servico Federal de Processamento de Dados", "SERPRO", "technology", 130),
    Company("Telecomunicacoes Brasileiras S.A.", "TELEBRAS", "technology", 132, True),
)


def _ascii(value: object) -> str:
    return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().upper()


def _br_number(value: str) -> float:
    value = value.strip().replace(" ", "")
    if value in {"-", ""}:
        return 0.0
    return float(value.replace(".", "").replace(",", "."))


def dividend_loss_measure(short_name: str, union_direct_dividends: float) -> float:
    """Return dividends forgone for the stake valued in a sale package.

    Petrobras RTN receipts cover the Union's direct 28.67% holding, while the
    maximal package values the full 36.61% state stake.  Scaling the direct
    receipt treats the 7.94% BNDES/BNDESPar holding as ultimately passed
    through to the Treasury; this is an upper bound because BNDES retains part
    of its profit.  BNDES's own RTN dividend line is not altered here.
    """
    if short_name == "PETROBRAS" and math.isfinite(union_direct_dividends):
        return union_direct_dividends * PETROBRAS_DIVIDEND_SCALE
    return union_direct_dividends


def nominal_gdp_by_year() -> dict[int, float]:
    fiscal = pd.read_csv(ROOT / "data/brazil/fiscal.csv").set_index("year")
    return {
        int(year): float(row.total_spending_r_millions) / (float(row.total_spending_pct_gdp) / 100)
        for year, row in fiscal.iterrows()
        if int(year) <= 2025
    }


def _deflator_to_2025() -> dict[int, float]:
    """Cumulative GDP-deflator factors to 2025 from archived/configured inputs."""
    raw = json.loads((ROOT / "data/raw/brazil/macro/ibge_sidra_6784.json").read_text(encoding="utf-8"))
    rows = raw[1:] if isinstance(raw, list) else raw.get("value", raw.get("data", []))
    rates: dict[int, float] = {}
    for row in rows:
        text = {str(k).lower(): v for k, v in row.items()}
        year_text = str(text.get("d3c", text.get("ano", text.get("year", ""))))
        value_text = next((v for k, v in text.items() if k in {"v", "valor", "value"}), None)
        if str(text.get("d2c", "")) == "9811" and year_text.isdigit() and value_text not in (None, "..."):
            try:
                rates[int(year_text)] = float(str(value_text).replace(",", "."))
            except ValueError:
                pass
    # Before the archived deflator series starts, derive the implicit deflator
    # from archived annual nominal GDP and real GDP growth.
    nominal_raw = json.loads((ROOT / "data/raw/brazil/macro/ibge_sidra_1846_gdp_current_1996_2025.json").read_text(encoding="utf-8"))[1:]
    nominal: dict[int, float] = {}
    for row in nominal_raw:
        if str(row.get("D2C")) == "585":
            year = int(str(row["D3C"])[:4])
            nominal[year] = nominal.get(year, 0.0) + float(str(row["V"]).replace(",", "."))
    growth_raw = json.loads((ROOT / "data/raw/brazil/backtest/worldbank_NY.GDP.MKTP.KD.ZG.json").read_text(encoding="utf-8"))[1]
    growth = {int(row["date"]): float(row["value"]) for row in growth_raw if row.get("value") is not None}
    for year in range(2016, 2021):
        rates.setdefault(year, ((nominal[year] / nominal[year - 1]) / (1 + growth[year] / 100) - 1) * 100)
    rates.update({2024: 3.8, 2025: 5.73})
    factors = {2025: 1.0}
    for year in range(2024, 2014, -1):
        factors[year] = factors[year + 1] * (1 + rates[year + 1] / 100)
    return factors


def read_dividends() -> pd.DataFrame:
    """Annual Union receipts, retaining RTN categories and payer detail where available."""
    path = RAW / "rtn_serie_historica_jul26.xlsx"
    frame = pd.read_excel(path, sheet_name="1.2", header=None)
    dates = pd.to_datetime(frame.iloc[4, 1:], errors="coerce")
    codes = {f"1.4.2.{i}": i for i in range(1, 10)}
    aliases = {
        1: "BB", 2: "BNB", 3: "BNDES", 4: "CAIXA", 5: "CORREIOS",
        6: "ELETROBRAS", 7: "IRB", 8: "PETROBRAS", 9: "OTHER_UNALLOCATED",
    }
    records: list[dict] = []
    for code, number in codes.items():
        hits = frame.index[frame.iloc[:, 0].astype(str).str.startswith(code)].tolist()
        if len(hits) != 1:
            raise ValueError(f"Expected one RTN row {code}; found {len(hits)}")
        values = pd.to_numeric(frame.iloc[hits[0], 1:], errors="coerce")
        monthly = pd.DataFrame({"date": dates, "value": values}).dropna(subset=["date"])
        annual = monthly.loc[monthly.date.dt.year.between(2015, 2025)].groupby(monthly.date.dt.year).value.sum()
        for year in range(2015, 2026):
            value = float(annual.get(year, 0.0))
            records.append({"company": aliases[number], "year": year, "union_dividends_brl_million": value,
                            "detail": "RTN named row" if number < 9 else "RTN other, not allocated by payer"})

    # Payer workbook splits the RTN 'other' category through April 2020.  It is
    # retained as additional detail, not added to the RTN totals.
    payer = RAW / "tesouro_dividendos_2015_abr2020.xlsx"
    months = {"JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO",
              "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO", "TOTAL", "EMPRESAS"}
    details: list[dict] = []
    for sheet in pd.ExcelFile(payer).sheet_names:
        data = pd.read_excel(payer, sheet_name=sheet, header=None)
        for row in data.itertuples(index=False, name=None):
            cells = [v for v in row if pd.notna(v)]
            if len(cells) < 2:
                continue
            label, value = str(cells[0]).strip(), cells[1]
            if _ascii(label) in months or "ATUALIZADA" in _ascii(label) or "RECEITAS" in _ascii(label):
                continue
            try:
                amount = float(value) / 1_000_000
            except (TypeError, ValueError):
                continue
            details.append({"company": _ascii(label).replace("PETROBRAS", "PETROBRAS"), "year": int(sheet),
                            "union_dividends_brl_million": amount, "detail": "payer detail; subset of RTN totals"})
    out = pd.concat([pd.DataFrame(records), pd.DataFrame(details)], ignore_index=True)
    gdp = nominal_gdp_by_year()
    factors = _deflator_to_2025()
    out["union_dividends_pct_gdp"] = out.apply(
        lambda r: r.union_dividends_brl_million / gdp[int(r.year)] * 100, axis=1)
    out["union_dividends_2025_brl_million"] = out.apply(
        lambda r: r.union_dividends_brl_million * factors[int(r.year)], axis=1)
    out["petrobras_regime"] = ""
    petro = out["company"].eq("PETROBRAS") & out["detail"].eq("RTN named row")
    out.loc[petro & out["year"].between(2015, 2020), "petrobras_regime"] = "2015-2020 low"
    out.loc[petro & out["year"].between(2021, 2025), "petrobras_regime"] = "2021-2025 high"
    return out.sort_values(["detail", "company", "year"], ignore_index=True)


def _raeef_financials() -> dict[str, dict[str, float]]:
    reader = PdfReader(RAW / "raeef_2021_2022.pdf")
    out: dict[str, dict[str, float]] = {}
    for company in COMPANIES:
        text = reader.pages[company.page - 1].extract_text() or ""
        equity = re.search(r"Patrim.nio L.quido Ajustado\s+(.+?)\n", text, re.IGNORECASE)
        transfer = re.search(r"Recursos Recebidos[^\n]*\s+(.+?)\n", text, re.IGNORECASE)
        result = re.search(r"Resultado L.quido\s+(.+?)\n", text, re.IGNORECASE)
        def latest(match: re.Match[str] | None) -> float:
            if match is None:
                return math.nan
            values = re.findall(r"-?\d[\d.]*,\d|-", match.group(1))
            return _br_number(values[-1]) / 1000 if values else math.nan  # R$ thousand -> million
        out[company.short] = {"book_equity_2021_brl_million": latest(equity),
                              "treasury_transfers_2021_brl_million": latest(transfer),
                              "net_income_2021_brl_million": latest(result)}
    return out


def _lead_match(short: str, lead: pd.DataFrame) -> pd.Series | None:
    tests = {
        "PETROBRAS": "Petrobras", "BB": "Banco do Brasil", "BNB": "Banco do Nordeste",
        "BASA": "Banco da Amazonia", "CAIXA": "Caixa", "CORREIOS": "Correios",
        "CMB": "Casa da Moeda", "SERPRO": "Serpro", "DATAPREV": "Dataprev",
        "TELEBRAS": "Telebras", "INFRAERO": "Infraero", "HEMOBRAS": "Hemobras",
        "FINEP": "Finep", "PPSA": "PPSA", "ABGF": "EMGEA; ABGF", "EMGEA": "EMGEA; ABGF",
        "CEAGESP": "CEAGESP", "CEASAMINAS": "Ceasaminas", "SPA": "Port authorities",
        "CDRJ": "Port authorities", "CODEBA": "Port authorities", "CDP": "Port authorities",
        "CDC": "Port authorities", "CODERN": "Port authorities", "AMAZUL": "ENBPar",
        "INB": "ENBPar", "NUCLEP": "ENBPar", "IMBEL": "IMBEL", "EMGEPRON": "Emgepron",
    }
    needle = tests.get(short)
    if needle:
        hit = lead.loc[lead.company.str.contains(re.escape(needle), case=False, regex=True)]
        if not hit.empty:
            return hit.iloc[0]
    return None


def _market_values() -> dict[str, tuple[float, float, str]]:
    def price(ticker: str) -> float:
        raw = json.loads((RAW / f"yahoo_chart_{ticker}.json").read_text(encoding="utf-8"))
        return float(raw["chart"]["result"][0]["meta"]["regularMarketPrice"])
    petro_total = 7_442_231_382 * price("PETR3.SA") + 5_602_042_788 * price("PETR4.SA")
    petro_stake = petro_total * PETROBRAS_STATE_STAKE_PCT / 100 / 1_000_000
    bb_stake = 5_730_834_040 * price("BBAS3.SA") * 0.5 / 1_000_000
    return {
        "PETROBRAS": (petro_stake, petro_stake, "2026-10-21 market prices; 36.61% state stake"),
        "BB": (bb_stake, bb_stake, "2026-10-21 market price; 50.0% Union stake"),
    }


def build_inventory(dividends: pd.DataFrame | None = None) -> pd.DataFrame:
    dividends = read_dividends() if dividends is None else dividends
    lead = pd.read_csv(ROOT / "data/brazil/soe_tiers_lead.csv")
    financials, market = _raeef_financials(), _market_values()
    payer = dividends.loc[dividends.detail.str.startswith("payer detail")].copy()
    named = dividends.loc[dividends.detail.eq("RTN named row")].copy()
    payer_alias = {"PETROBRAS": "PETROBRAS", "BB": "BB", "BNDES": "BNDES", "BNB": "BNB",
                   "CAIXA": "CAIXA", "CORREIOS": "CORREIOS", "DATAPREV": "DATAPREV",
                   "EMGEPRON": "EMGEPRON", "SERPRO": "SERPRO", "INFRAERO": "INFRAERO"}
    rows = []
    for company in COMPANIES:
        match = _lead_match(company.short, lead)
        dependent = company.dependent if match is None else str(match.dependent).lower() == "yes"
        tier = str(match.tier) if match is not None else ("D" if dependent else "C")
        flag = "" if match is not None else "unmatched to lead tier; default D if dependent, else C"
        stake_text = str(match.union_stake_total_pct) if match is not None else ("100.0" if not company.short == "ELETROBRAS" else "0.0")
        try:
            stake = float(stake_text)
        except ValueError:
            stake = math.nan
            flag = (flag + "; Union stake requires verification").strip("; ")
        f = financials[company.short]
        if company.short in market:
            low, high, basis = market[company.short]
        elif not dependent and math.isfinite(f["book_equity_2021_brl_million"]) and f["book_equity_2021_brl_million"] > 0:
            fraction = stake / 100 if math.isfinite(stake) else 1.0
            low = f["book_equity_2021_brl_million"] * fraction * P_TO_B_RANGE[0]
            high = f["book_equity_2021_brl_million"] * fraction * P_TO_B_RANGE[1]
            basis = "RAEEF 2021 book equity x assumed P/B 0.5-1.5; dated"
        else:
            low = high = math.nan
            basis = "not valued: dependent, non-positive/missing equity, or missing stake"
        aliases = [k for k, v in payer_alias.items() if v == company.short]
        observed = payer.loc[payer.company.isin(aliases)]
        direct = named.loc[named.company.eq(company.short)]
        series = direct if not direct.empty else observed
        total = float(series.union_dividends_brl_million.sum()) if not series.empty else math.nan
        direct_real_average = float(series.groupby("year").union_dividends_2025_brl_million.sum().mean()) if not series.empty else math.nan
        real_average = dividend_loss_measure(company.short, direct_real_average)
        status = "verify"
        if company.short == "ELETROBRAS":
            status = "privatised_2022; no longer directly controlled"
        elif company.short == "CODESA":
            status = "privatised_2022; no longer directly controlled"
        elif company.short in {"EPL", "VALEC", "CPRM"}:
            status = "verify: reorganisation/renaming since bulletin"
        rows.append({
            "company": company.name, "short_name": company.short, "group": company.group,
            "dependent": dependent, "tier": tier,
            "status_2026": status, "tier_flag": flag,
            "union_stake_pct": stake, "valuation_low_brl_million": low,
            "valuation_mid_brl_million": (low + high) / 2 if math.isfinite(low) else math.nan,
            "valuation_high_brl_million": high, "valuation_basis": basis,
            "union_dividends_2015_2025_brl_million": total,
            "cycle_average_dividends_2025_brl_million": real_average,
            "dividend_coverage": (f"{int(series.year.min())}-{int(series.year.max())}" if not series.empty else "not identified"),
            "treasury_transfers_latest_brl_million": f["treasury_transfers_2021_brl_million"],
            "treasury_transfers_year": 2021, "book_equity_2021_brl_million": f["book_equity_2021_brl_million"],
            "net_income_2021_brl_million": f["net_income_2021_brl_million"], "raeef_page": company.page,
        })
    result = pd.DataFrame(rows)
    gdp = nominal_gdp_by_year()[2025]
    result["union_dividends_2015_2025_pct_gdp_sum"] = result["union_dividends_2015_2025_brl_million"] / gdp * 100
    result["cycle_average_dividend_yield_pct"] = (
        result["cycle_average_dividends_2025_brl_million"] / result["valuation_mid_brl_million"] * 100
    )
    return result


def package_members(inventory: pd.DataFrame, package: str) -> pd.DataFrame:
    if package not in PACKAGES:
        raise ValueError(f"Unknown privatisation package: {package}")
    active = inventory.loc[~inventory.status_2026.str.startswith("privatised")].copy()
    if package == "f5":
        return active.loc[active.tier.eq("A")]
    excluded = {"PETROBRAS", "BB", "CAIXA", "BNDES", "BNB", "BASA"}
    members = active.loc[active.tier.isin(["A", "B"]) & ~active.short_name.isin(excluded)]
    if package == "broad_bb_petrobras":
        members = pd.concat([members, active.loc[active.short_name.isin(["BB", "PETROBRAS"])]]).drop_duplicates("short_name")
    return members


def sale_paths(
    inventory: pd.DataFrame,
    package: str,
    rng: np.random.Generator,
    nominal_gdp_brl_million: float,
    *,
    f5_target_pp: float | None = None,
    base_year: int = 2025,
    end_year: int = 2046,
    petroleum_factor_by_year: Mapping[int, float] | None = None,
) -> dict:
    """Draw company sales and return pp-GDP stock and revenue paths.

    Each completed company is sold in equal tranches across 2027-30 (tier A)
    or 2028-30 (tier B).  Dividends on a tranche stop the following year.
    """
    members = package_members(inventory, package)
    values = members.valuation_mid_brl_million.fillna(0.0)
    scale = 1.0
    if package == "f5":
        target = max(0.0, float(f5_target_pp or 0.0)) / 100 * nominal_gdp_brl_million
        scale = min(1.0, target / values.sum()) if values.sum() > 0 else 0.0
    proceeds = {year: 0.0 for year in range(base_year, end_year + 1)}
    lost = {year: 0.0 for year in range(base_year, end_year + 1)}
    detail = []
    for row in members.itertuples():
        value = float(row.valuation_mid_brl_million) if math.isfinite(row.valuation_mid_brl_million) else 0.0
        if value <= 0:
            continue
        probability = float(rng.uniform(*TIER_B_COMPLETION_RANGE)) if row.tier == "B" else 1.0
        completed = bool(rng.random() < probability) if row.tier == "B" else True
        discount = float(rng.uniform(*DISCOUNT_RANGE))
        sold_fraction = scale if completed else 0.0
        years = SALE_YEARS[1:] if row.tier == "B" else SALE_YEARS
        annual_proceeds = value * sold_fraction * (1 - discount) / len(years)
        dividend = float(row.cycle_average_dividends_2025_brl_million)
        if not math.isfinite(dividend):
            dividend = 0.0
        for sale_year in years:
            proceeds[sale_year] += annual_proceeds
            tranche_dividend = dividend * sold_fraction / len(years)
            for year in range(sale_year + 1, end_year + 1):
                factor = (petroleum_factor_by_year or {}).get(year, 1.0) if row.short_name == "PETROBRAS" else 1.0
                lost[year] -= tranche_dividend * factor
        detail.append({"company": row.short_name, "tier": row.tier, "completion_probability": probability,
                       "completed": completed, "discount": discount, "sold_fraction": sold_fraction})
    return {
        "debt_adjustment_by_year": {year - base_year: value / nominal_gdp_brl_million * 100 for year, value in proceeds.items() if year > base_year},
        "non_tax_revenue_by_year": {year - base_year: value / nominal_gdp_brl_million * 100 for year, value in lost.items() if year > base_year},
        "companies": detail,
    }


def deterministic_package_table(inventory: pd.DataFrame) -> pd.DataFrame:
    gdp = nominal_gdp_by_year()[2025]
    rows = []
    for package in PACKAGES:
        members = package_members(inventory, package)
        value = float(members.valuation_mid_brl_million.sum())
        dividend = float(members.cycle_average_dividends_2025_brl_million.fillna(0).sum())
        rows.append({"package": package, "companies": len(members), "value_brl_billion": value / 1000,
                     "value_pct_gdp": value / gdp * 100, "dividends_brl_billion": dividend / 1000,
                     "dividend_yield_pct": dividend / value * 100 if value else math.nan})
    return pd.DataFrame(rows)


def _markdown(frame: pd.DataFrame, decimals: int = 3) -> str:
    def cell(value: object) -> str:
        if isinstance(value, (float, np.floating)):
            return "" if not math.isfinite(float(value)) else f"{float(value):.{decimals}f}"
        return str(value)
    header = "| " + " | ".join(frame.columns) + " |"
    rule = "|" + "|".join("---" for _ in frame.columns) + "|"
    rows = ["| " + " | ".join(cell(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *rows])


def _oil_summary() -> tuple[float, float, float]:
    raw = json.loads((RAW / "ipeadata_ANP12_PDPET12.json").read_text(encoding="utf-8"))["value"]
    frame = pd.DataFrame({"year": [int(r["VALDATA"][:4]) for r in raw], "value": [float(r["VALVALOR"]) for r in raw]})
    annual = frame.loc[frame.year.between(2002, 2026)].groupby("year").value.mean()
    return float(annual.loc[2002]), float(annual.loc[2025]), float(annual.loc[2026])


def render_report(inventory: pd.DataFrame) -> str:
    packages = deterministic_package_table(inventory)
    tiers = inventory.groupby("tier", as_index=False).agg(companies=("company", "size"),
        valued_stakes_brl_billion=("valuation_mid_brl_million", lambda x: x.sum() / 1000))
    rate_fixed = 5.05
    i1 = yaml.safe_load((ROOT / "config/i1_proposed.yaml").read_text(encoding="utf-8"))
    i1_rates = {int(r["year"]): rate_fixed + float(r["difference_from_fixed_5_05_pp"])
                for r in i1["s0_path_before_fiscal_term"] if 2027 <= int(r["year"]) <= 2030}
    oil_2002, oil_2025, oil_2026 = _oil_summary()
    dividends = read_dividends()
    petro = dividends.loc[
        dividends.company.eq("PETROBRAS") & dividends.detail.eq("RTN named row")
    ]
    petro_low_direct = float(petro.loc[petro.year.between(2015, 2020), "union_dividends_2025_brl_million"].mean()) / 1000
    petro_high_direct = float(petro.loc[petro.year.between(2021, 2025), "union_dividends_2025_brl_million"].mean()) / 1000
    petro_low_full = dividend_loss_measure("PETROBRAS", petro_low_direct)
    petro_high_full = dividend_loss_measure("PETROBRAS", petro_high_direct)
    lines = [
        "# Privatisation of federal state-owned companies", "",
        "This note evaluates measures, not candidates. The `f5` package represents the case-by-case programme; broader packages are sensitivities. Amounts use the midpoint of the stated valuation range and are not sale forecasts.", "",
        "## Inventory by legal tier", "", _markdown(tiers, 2), "",
        "Tier A has an existing authority/PND route; tier B needs a specific law; tier C is excluded or strategic; tier D is Treasury-dependent and not treated as saleable. The source bulletin lists 46 directly controlled companies. Eletrobras and CODESA are marked as no longer directly controlled; uncertain reorganisations remain `verify` in the inventory.", "",
        "## Saleable state stakes", "", _markdown(packages, 3), "",
        "The `f5` Monte Carlo path remains capped by the existing 0-2 pp of GDP F5 range and draws tier-A stakes value-weightedly. `broad` adds eligible tier-B companies but excludes Petrobras and Banco do Brasil. `broad_bb_petrobras` adds BB control and the full 36.61% state stake in Petrobras; that Petrobras stake includes Union, BNDES and BNDESPar holdings once.", "",
        "## Annual flow arithmetic", "",
        "Interest saved equals sale value times the rate; dividends lost equal the 2015-2025 cycle measure available for the selected stakes. This deterministic comparison applies no block discount or completion haircut.", "",
        "| package | fixed-rate interest saved (R$ bn/yr) | dividends lost (R$ bn/yr) | break-even dividend yield | I1 2027-30 interest saved range (R$ bn/yr) |", "|---|---:|---:|---:|---:|",
    ]
    for row in packages.itertuples():
        fixed = row.value_brl_billion * rate_fixed / 100
        i1_values = [row.value_brl_billion * rate / 100 for rate in i1_rates.values()]
        lines.append(f"| {row.package} | {fixed:.3f} | {row.dividends_brl_billion:.3f} | {row.dividend_yield_pct:.3f}% | {min(i1_values):.3f}-{max(i1_values):.3f} |")
    lines += ["", f"At the fixed S0 real rate, the break-even yield is {rate_fixed:.2f}% before transaction discounts: above it, foregone dividends exceed first-year interest savings; below it, interest savings exceed dividends. The I1 comparison uses its 2027-2030 real debt-rate path ({min(i1_rates.values()):.2f}%-{max(i1_rates.values()):.2f}%).", "",
        "Asset-sale receipts reduce gross debt. They do not create an equal improvement in public-sector net worth: at a fair price the state exchanges an equity asset for lower liabilities. The recurring fiscal flow is therefore shown separately as interest saved less dividends lost.", "",
        "## Petrobras and oil", "",
        f"ANP monthly data average {oil_2002:,.0f} thousand barrels/day in 2002, {oil_2025:,.0f} in 2025, and {oil_2026:,.0f} through August 2026. Real direct-Union Petrobras receipts averaged R${petro_low_direct:.3f}bn a year in the 2015-2020 low regime and R${petro_high_direct:.3f}bn in the 2021-2025 high regime (2025 reais). For the full 36.61% state stake, the corresponding lost-dividend measures are R${petro_low_full:.3f}bn and R${petro_high_full:.3f}bn, scaling the direct receipts by 36.61/28.67. This treats Petrobras dividends received through BNDES and BNDESPar as passed through to the Treasury, an upper bound because BNDES retains part of its profit. Royalties, special participation and taxes accrue to the state whoever owns Petrobras; only the dividend share depends on ownership. In model runs Petrobras dividends follow the already-drawn C7 commodity-price path; ownership is not assumed to change production.", "",
        "## Evidence qualifications", "",
        "Unlisted valuations use 2021 RAEEF book equity and an assumed 0.5-1.5 price-to-book range. Payer detail ends in April 2020, so later RTN 'other' receipts cannot be assigned to individual companies and are not invented. Correios was non-dependent in RAEEF 2021: the default saving from ending Treasury-covered operating losses is zero. Postalis is shown only as a 0-R$7.799bn documented contingent-liability sensitivity, not as proceeds or a certain public cost.", ""]
    return "\n".join(lines)


def render_method() -> str:
    return """# Privatisation module method

## Accounting

For each completed sale, discounted proceeds reduce gross debt in the sale year. The sold tranche's Union dividends stop in the following year and enter `non_tax_revenue_by_year` with a negative sign. That flow changes the primary balance in C2, C6 and C5, but is excluded from household tax incidence and the revenue multiplier. The same path builder is used for every scenario that defines a package.

## Assumptions

| Assumed number or rule | Value | Basis |
|---|---:|---|
| Unlisted price-to-book range | 0.5-1.5 | Task PZ prespecification; applied to RAEEF 2021 adjusted book equity |
| Block-sale discount | uniform 0%-15% | Task PZ prespecification; no sourced distribution claimed |
| Tier-B completion probability | probability drawn uniform 0.3-0.8, then Bernoulli | Task PZ prespecification; Eletrobras took about five years and the Correios bill has stalled since 2021 |
| Sale timing | tier A: 2027-2030; tier B: 2028-2030; equal tranches | Task PZ timing; equal tranches are the neutral implementation of “spread over” the period |
| F5 size | existing uniform 0-2 pp GDP draw, capped by available tier-A midpoint value | Existing programme F5 range; PZ requires tier-A, value-weighted proceeds |
| Dividends | real annual mean of identified receipts; unassigned receipts not allocated | Archived RTN series and payer workbook; avoids inventing payer shares |
| Petrobras full state stake | 36.61% of total capital | Petrobras profile; Union direct plus BNDES and BNDESPar holdings |
| Petrobras Union direct stake | 28.67% of total capital | 36.61% full state stake less 7.94% indirect holding through BNDES and BNDESPar |
| Petrobras lost-dividend scale | 36.61 / 28.67 = 1.276945 | Applies the full-state/direct-stake ratio to RTN line 1.4.2.8; treats BNDES as passing those Petrobras dividends through to the Treasury, an upper bound because BNDES retains part of its profit; BNDES's own dividend line is unchanged and BNDES is not sold |
| Correios Treasury-covered operating loss | 0 | RAEEF identifies Correios as non-dependent; no evidence in the supplied files that Treasury covered the later reported loss |
| Postalis contingent liability | R$0-R$7.79919bn | Lower bound assumes no transfer to the state; upper bound is the 2021 accumulated technical deficit on RAEEF p.91 |
| Petrobras ownership | full state stake sold once; no BNDES double count | Petrobras fact sheet figures recorded in SOURCES.md; BNDES and BNDESPar are represented only through Petrobras's 7.94% indirect holding |
| Banco do Brasil ownership | Union stake 50.0% | BB results figure recorded in SOURCES.md |
| Debt-interest comparator | S0 fixed real rate 5.05%; I1 annual path separately | Existing model rate and `config/i1_proposed.yaml` |

## Sources and construction

The inventory is the 46 directly controlled companies listed on SEST bulletin pp.28-29. Company financials use RAEEF 2021-22 company pages recorded in `raeef_page`; dependent-budget evidence is on bulletin p.25. Market values use archived 2026-10-21 prices only when supplied share counts permit a value. Annual Union receipts use RTN sheet 1.2 codes 1.4.2.1-1.4.2.9; the payer workbook provides the partial split of “other” receipts for 2015-April 2020.

## Limitations

Unlisted valuations are dated and are ranges, not appraisals. Later “other” dividends cannot be allocated by company. The module estimates neither efficiency nor product-price effects of privatisation on GDP beyond the model's existing wage channel. It imposes no change in Petrobras investment or production by owner; that contested effect is not estimated. Legal tiers are supplied lead-developer classifications, and rows unmatched to them are explicitly defaulted and flagged. Gross-debt reduction must not be read as an equal net-worth gain.
"""


def main() -> int:
    dividends = read_dividends()
    inventory = build_inventory(dividends)
    DIVIDENDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    dividends.to_csv(DIVIDENDS_PATH, index=False, float_format="%.6f")
    inventory.to_csv(INVENTORY_PATH, index=False, float_format="%.6f")
    REPORT_PATH.write_text(render_report(inventory), encoding="utf-8")
    DOC_PATH.write_text(render_method(), encoding="utf-8")
    print(f"Wrote {len(inventory)} companies, {len(dividends)} dividend rows, and PZ reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
