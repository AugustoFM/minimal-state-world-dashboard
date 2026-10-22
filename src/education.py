"""Education data, estimates, and deterministic programme channels (ED).

The module is deliberately not wired into Monte Carlo.  Running
``python -m src.education`` rebuilds every ED-owned data and report output
from archived inputs.  Schooling effects call C5's implementation directly.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from src.feedback import schooling_log_output_effect
from src.baseline import project_baseline
from src.macro import baseline_real_gdp_path, load_macro_inputs, macro_input
from src import programs


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/brazil/education"
PATHS = {
    "panel": ROOT / "data/brazil/education_panel.csv",
    "estimates": ROOT / "data/brazil/education_estimates.csv",
    "scenarios": ROOT / "data/brazil/education_scenarios.csv",
    "config": ROOT / "config/ed_proposed.yaml",
    "report": ROOT / "outputs/education.md",
    "docs": ROOT / "docs/education.md",
}
VARIANTS = ("low", "central", "high")
LEVEL_MAP = {
    "Total": "total",
    "Sem instrução e menos de 1 ano de estudo": "below_fundamental",
    "Ensino fundamental incompleto ou equivalente": "below_fundamental",
    "Sem instrução e fundamental incompleto": "below_fundamental",
    "Sem instrução e fundamental incompleto ou equivalente": "below_fundamental",
    "Ensino fundamental completo ou equivalente": "fundamental_secondary_incomplete",
    "Ensino médio incompleto ou equivalente": "fundamental_secondary_incomplete",
    "Fundamental completo e médio incompleto": "fundamental_secondary_incomplete",
    "Fundamental completo e médio incompleto ou equivalente": "fundamental_secondary_incomplete",
    "Ensino médio completo ou equivalente": "secondary_higher_incomplete",
    "Ensino superior incompleto ou equivalente": "secondary_higher_incomplete",
    "Médio completo e superior incompleto": "secondary_higher_incomplete",
    "Médio completo ou equivalente e superior incompleto": "secondary_higher_incomplete",
    "Ensino superior completo ou equivalente": "higher_complete",
    "Superior completo": "higher_complete",
}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _number(value: object) -> float:
    if value in (None, "-", "...", "..", "X"):
        return math.nan
    return float(str(value).replace(",", "."))


def _plain(text: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in normalized if not unicodedata.combining(c)).upper()


def parse_sidra(path: str | Path) -> pd.DataFrame:
    """Parse SIDRA v3 result JSON into one row per geography-period-category."""
    obj = _read_json(path)
    variables = obj if isinstance(obj, list) else [obj]
    rows: list[dict[str, object]] = []
    for variable in variables:
        for result in variable.get("resultados", []):
            classes: dict[str, str] = {}
            for classification in result.get("classificacoes", []):
                values = list(classification.get("categoria", {}).values())
                classes[str(classification.get("nome"))] = " | ".join(map(str, values))
            for series in result.get("series", []):
                location = series["localidade"]
                for period, value in series.get("serie", {}).items():
                    rows.append({
                        "variable": variable.get("variavel"),
                        "unit": variable.get("unidade"),
                        "geography_level": location["nivel"]["nome"],
                        "geography_code": str(location["id"]),
                        "geography": location["nome"],
                        "period": str(period),
                        "value": _number(value),
                        **classes,
                    })
    return pd.DataFrame(rows)


def rescale_2024_source_units(
    frame: pd.DataFrame, value_col: str = "value", already_brl: bool = False
) -> pd.DataFrame:
    """Convert raw Tesouro 2024 R$ million observations to reais exactly once.

    The archived aggregate uses ``value_brl`` and is already converted; callers
    parsing the untouched source should leave ``already_brl=False``.
    """
    out = frame.copy()
    if not already_brl:
        years = pd.to_numeric(out["ANO"], errors="raise")
        out.loc[years.eq(2024), value_col] = (
            pd.to_numeric(out.loc[years.eq(2024), value_col], errors="raise") * 1_000_000
        )
    return out


def _ipca_annual_average_index() -> pd.Series:
    raw = pd.DataFrame(_read_json(ROOT / "data/raw/brazil/rates/bcb_sgs_433_ipca_monthly.json"))
    raw["date"] = pd.to_datetime(raw["data"], dayfirst=True, errors="raise")
    raw["inflation"] = pd.to_numeric(raw["valor"], errors="raise") / 100
    raw = raw.sort_values("date")
    raw["index"] = (1 + raw["inflation"]).cumprod()
    return raw.groupby(raw["date"].dt.year)["index"].mean()


def read_cofog_real() -> pd.DataFrame:
    """Read the archived aggregate and express flows in average-2024 reais."""
    frame = pd.read_csv(
        RAW / "tesouro_cofog_gc_2010_2024_aggregated.csv.gz",
        dtype={"UNIDADE ORCAMENTARIA": str},
    )
    # The archive creator already converted the source's 2024 R$ million rows.
    frame = rescale_2024_source_units(frame, "value_brl", already_brl=True)
    index = _ipca_annual_average_index()
    frame["value_real_2024"] = frame["value_brl"] * frame["ANO"].map(index.loc[2024] / index)
    return frame


def spending_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    description = frame["UNIDADE ORCAMENTARIA DESCRICAO"].fillna("").map(_plain)
    function = frame["CLASSIFICACAO COFOG DESCRICAO"].fillna("").map(_plain)
    code = frame["UNIDADE ORCAMENTARIA"].fillna("").astype(str).str.zfill(5)
    university = description.str.contains(r"UNIV", regex=True) & ~description.str.contains(
        r"HOSP|EBSERH", regex=True
    )
    federal_network = (
        description.str.contains(r"INSTITUTO FEDERAL|INST[.]?FED", regex=True)
        | description.str.contains(r"CENTRO FED.*EDUC.*TECNOL|CEFET", regex=True)
        | description.str.contains("COLEGIO PEDRO II", regex=False)
    )
    personnel = frame["CLASSIFICACAO ECONOMICA GFS DESCRICAO"].fillna("").map(_plain).str.contains(
        r"REMUNERACAO|BENEFICIOS SOCIAIS", regex=True
    )
    return {
        "university": university,
        "federal_network": federal_network,
        "mcti": code.str.startswith("24"),
        "personnel": personnel,
        "tertiary": function.str.contains("EDUCACAO - ENSINO SUPERIOR", regex=False),
        "secondary": function.str.contains("ENSINO FUNDAMENTAL II E MEDIO", regex=False),
        "vocational": function.str.contains("ENSINO POS-SECUNDARIO E NAO SUPERIOR", regex=False),
        "fies": code.eq("74902"),
    }


def calibration_table(frame: pd.DataFrame | None = None) -> pd.DataFrame:
    """Recompute real university, non-personnel, IF and MCTI spending records."""
    data = read_cofog_real() if frame is None else frame.copy()
    masks = spending_masks(data)
    definitions = {
        "federal_universities_total": masks["university"],
        "federal_universities_nonpersonnel": masks["university"] & ~masks["personnel"],
        "federal_institutes_total": masks["federal_network"],
        "mcti_budget_units": masks["mcti"],
        "cofog_tertiary": masks["tertiary"],
    }
    rows = []
    for item, mask in definitions.items():
        annual = data.loc[mask].groupby("ANO")["value_real_2024"].sum() / 1e9
        row: dict[str, object] = {"item": item}
        for year in (2018, 2019, 2022, 2024):
            row[f"r_bn_{year}"] = float(annual.get(year, math.nan))
        row["change_2018_2022_pct"] = (row["r_bn_2022"] / row["r_bn_2018"] - 1) * 100
        row["change_2022_2024_pct"] = (row["r_bn_2024"] / row["r_bn_2022"] - 1) * 100
        rows.append(row)
    return pd.DataFrame(rows)


def _category(frame: pd.DataFrame, name: str) -> pd.Series:
    if name not in frame:
        return pd.Series("", index=frame.index, dtype=str)
    return frame[name].fillna("").astype(str)


def _annual_entrepreneur_rates() -> pd.DataFrame:
    occupied = parse_sidra(RAW / "ibge_sidra_4095_occupied_by_education_quarterly.json")
    occupied["level"] = _category(occupied, "Nível de instrução").map(LEVEL_MAP)
    occupied = occupied.dropna(subset=["level", "value"])
    occupied["year"] = occupied["period"].str[:4].astype(int)
    occupied = occupied.groupby(
        ["geography_level", "geography_code", "geography", "period", "year", "level"], as_index=False
    )["value"].sum().rename(columns={"value": "occupied_thousand"})
    # Table 4095 is quarterly; entrepreneur tables are annual averages.
    occupied = occupied.groupby(
        ["geography_level", "geography_code", "geography", "year", "level"], as_index=False
    )["occupied_thousand"].mean()
    files = {
        "entrepreneur_rate_pct": "ibge_sidra_7193_entrepreneurs_by_education.json",
        "employer_rate_pct": "ibge_sidra_7195_entrepreneurs_by_education.json",
        "cnpj_employer_rate_pct": "ibge_sidra_7196_entrepreneurs_by_education.json",
        "own_account_rate_pct": "ibge_sidra_7247_entrepreneurs_by_education.json",
        "cnpj_own_account_rate_pct": "ibge_sidra_7248_entrepreneurs_by_education.json",
    }
    keys = ["geography_level", "geography_code", "geography", "year", "level"]
    out = occupied
    for indicator, filename in files.items():
        numerator = parse_sidra(RAW / filename)
        numerator["level"] = _category(numerator, "Nível de instrução").map(LEVEL_MAP)
        numerator["year"] = numerator["period"].str[:4].astype(int)
        numerator = numerator.dropna(subset=["level", "value"])[keys + ["value"]]
        numerator = numerator.rename(columns={"value": indicator.replace("_rate_pct", "_thousand")})
        out = out.merge(numerator, on=keys, how="left", validate="one_to_one")
        num = indicator.replace("_rate_pct", "_thousand")
        out[indicator] = 100 * out[num] / out["occupied_thousand"]
    rates = [*files]
    return out[["geography_level", "geography_code", "geography", "year", "level", *rates]]


def composition_change(
    start_shares: Mapping[str, float], end_shares: Mapping[str, float], fixed_rates: Mapping[str, float]
) -> float:
    """Percentage-point rate change from composition only; shares are percentages."""
    levels = set(start_shares) | set(end_shares) | set(fixed_rates)
    if any(level not in start_shares or level not in end_shares or level not in fixed_rates for level in levels):
        raise ValueError("start shares, end shares, and rates must cover identical levels")
    if not math.isclose(sum(start_shares.values()), 100.0, abs_tol=0.2):
        raise ValueError("start shares must sum to 100")
    if not math.isclose(sum(end_shares.values()), 100.0, abs_tol=0.2):
        raise ValueError("end shares must sum to 100")
    return sum((float(end_shares[k]) - float(start_shares[k])) * float(fixed_rates[k]) / 100 for k in levels)


def _attainment() -> tuple[pd.DataFrame, pd.DataFrame]:
    years = parse_sidra(RAW / "ibge_sidra_7126_mean_years_schooling_2016_2025.json")
    years["year"] = years["period"].astype(int)
    years["age_group"] = _category(years, "Grupo de idade")
    distribution = parse_sidra(RAW / "ibge_sidra_7267_education_level_2016_2025.json")
    distribution["year"] = distribution["period"].astype(int)
    distribution["level"] = _category(distribution, "Nível de instrução").map(LEVEL_MAP)
    distribution = distribution.dropna(subset=["level"])
    distribution = distribution.loc[~distribution["level"].eq("total")]
    return years, distribution


def _crime_panel(years: pd.DataFrame) -> pd.DataFrame:
    crime = pd.read_csv(ROOT / "data/raw/brazil/crime/ipeadata_atlas_violencia_homicides.csv.gz")
    state = crime.loc[crime["level"].eq("Estados") & crime["year"].between(2016, 2024)]
    wide = state.pivot_table(index=["territory_code", "year"], columns="series", values="value").reset_index()
    # A youth-homicide rate on the available common denominator (all residents).
    wide["youth_homicides_per_100k_residents"] = (
        wide["AVIOL12_HOMICJ"] / wide["AVIOL12_HOMIC"] * wide["AVIOL12_THOMIC"]
    )
    edu = years.loc[
        years["geography_level"].eq("Unidade da Federação") & years["age_group"].eq("18 a 24 anos"),
        ["geography_code", "geography", "year", "value"],
    ].rename(columns={"value": "mean_years_18_24"})
    edu["territory_code"] = pd.to_numeric(edu["geography_code"], errors="raise")
    return edu.merge(wide, on=["territory_code", "year"], how="inner", validate="one_to_one")


def fixed_effects_clustered(
    frame: pd.DataFrame, dependent: str, regressor: str, entity: str, time: str
) -> dict[str, float | int]:
    """Two-way fixed-effects OLS with entity-clustered covariance."""
    sample = frame[[dependent, regressor, entity, time]].dropna().copy()
    entities = pd.get_dummies(sample[entity].astype(str), drop_first=True, dtype=float)
    times = pd.get_dummies(sample[time].astype(str), drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(sample)), sample[regressor].to_numpy(float), entities, times])
    y = sample[dependent].to_numpy(float)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    bread = np.linalg.pinv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    groups = sample[entity].to_numpy()
    for group in np.unique(groups):
        score = x[groups == group].T @ residual[groups == group]
        meat += np.outer(score, score)
    g, n, k = len(np.unique(groups)), len(sample), x.shape[1]
    correction = (g / (g - 1)) * ((n - 1) / (n - k)) if g > 1 and n > k else 1.0
    covariance = correction * bread @ meat @ bread
    se = float(np.sqrt(max(covariance[1, 1], 0)))
    return {"estimate": float(beta[1]), "std_error": se, "nobs": n, "clusters": g}


def _firm_rates() -> pd.DataFrame:
    source = pd.read_csv(ROOT / "data/brazil/firm_distress_annual.csv")
    columns = [
        "firm_birth_rate_pct", "firm_entry_rate_pct", "firm_exit_rate_pct",
        "employer_birth_rate_pct", "employer_death_rate_pct",
    ]
    return source[["year", *columns]].melt("year", var_name="indicator", value_name="value").dropna()


def _spending_panel(cofog: pd.DataFrame) -> pd.DataFrame:
    masks = spending_masks(cofog)
    rows = []
    for indicator in ("tertiary", "secondary", "vocational", "fies"):
        annual = cofog.loc[masks[indicator]].groupby("ANO")["value_real_2024"].sum() / 1e9
        for year in range(2010, 2025):
            rows.append({"year": year, "indicator": f"real_{indicator}_spending_r_bn_2024",
                         "value": float(annual.get(year, 0.0))})
    # The COFOG extract cannot identify Pe-de-Meia as a separate line. Do not invent it.
    for year in range(2010, 2025):
        rows.append({"year": year, "indicator": "real_pe_de_meia_spending_r_bn_2024", "value": math.nan})
    return pd.DataFrame(rows)


def build_panel() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    years, distribution = _attainment()
    entrepreneurship = _annual_entrepreneur_rates()
    crime = _crime_panel(years)
    pieces: list[pd.DataFrame] = []
    a = years.rename(columns={"age_group": "detail"})
    a["indicator"] = "mean_years_schooling"
    pieces.append(a[["year", "geography_level", "geography_code", "geography", "indicator", "detail", "value"]])
    d = distribution.rename(columns={"level": "detail"})
    d["indicator"] = "education_share_pct"
    pieces.append(d[["year", "geography_level", "geography_code", "geography", "indicator", "detail", "value"]])
    rate_cols = [c for c in entrepreneurship if c.endswith("_rate_pct")]
    e = entrepreneurship.melt(
        ["geography_level", "geography_code", "geography", "year", "level"],
        value_vars=rate_cols, var_name="indicator", value_name="value",
    ).rename(columns={"level": "detail"})
    pieces.append(e[["year", "geography_level", "geography_code", "geography", "indicator", "detail", "value"]])
    c = crime.rename(columns={"mean_years_18_24": "schooling_value"})
    for indicator, column in [
        ("mean_years_schooling_18_24", "schooling_value"),
        ("youth_homicides_per_100k_residents", "youth_homicides_per_100k_residents"),
    ]:
        temp = c[["year", "geography_code", "geography", column]].rename(columns={column: "value"})
        temp["geography_level"] = "Unidade da Federação"
        temp["indicator"] = indicator
        temp["detail"] = "18-24" if "schooling" in indicator else "youth 15-29; all-resident denominator"
        pieces.append(temp[["year", "geography_level", "geography_code", "geography", "indicator", "detail", "value"]])
    for simple, level in [(_firm_rates(), "Brasil"), (_spending_panel(read_cofog_real()), "Governo central")]:
        simple["geography_level"] = level
        simple["geography_code"] = "1"
        simple["geography"] = "Brasil"
        simple["detail"] = ""
        pieces.append(simple[["year", "geography_level", "geography_code", "geography", "indicator", "detail", "value"]])
    panel = pd.concat(pieces, ignore_index=True).sort_values(
        ["indicator", "geography_level", "geography_code", "detail", "year"], ignore_index=True
    )
    return panel, {"years": years, "distribution": distribution, "entrepreneurship": entrepreneurship, "crime": crime}


def build_estimates(parts: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    rates = parts["entrepreneurship"]
    br = rates.loc[
        rates["geography"].eq("Brasil") & rates["year"].between(2012, 2025)
        & ~rates["level"].eq("total")
    ]
    fixed = br.groupby("level")["employer_rate_pct"].mean().to_dict()
    distribution = parts["distribution"]
    shares: dict[int, dict[str, float]] = {}
    for year in (2016, 2025):
        shares[year] = distribution.loc[
            distribution["geography"].eq("Brasil") & distribution["year"].eq(year)
        ].set_index("level")["value"].to_dict()
    comp = composition_change(shares[2016], shares[2025], fixed)
    rows: list[dict[str, object]] = [{
        "analysis": "composition", "specification": "2016_to_2025_fixed_2012_2025_rates",
        "term": "employer_rate_change_pp", "estimate": comp, "std_error": math.nan,
        "nobs": len(br), "unit": "percentage points",
        "note": "descriptive composition arithmetic; not causal",
    }]
    for indicator in ("employer_rate_pct", "cnpj_employer_rate_pct"):
        for level, value in br.groupby("level")[indicator].mean().items():
            rows.append({
                "analysis": "education_gradient", "specification": indicator,
                "term": level, "estimate": value, "std_error": math.nan,
                "nobs": int(br.loc[br["level"].eq(level), indicator].notna().sum()),
                "unit": "percent of occupied in level", "note": "national annual mean",
            })
    crime = fixed_effects_clustered(
        parts["crime"], "youth_homicides_per_100k_residents", "mean_years_18_24",
        "territory_code", "year",
    )
    rows.append({
        "analysis": "crime_association", "specification": "state_and_year_fe_cluster_state",
        "term": "mean_years_18_24", **crime,
        "unit": "youth homicides per 100k residents per school year",
        "note": "association, not causal; youth deaths use all-resident denominator",
    })
    return pd.DataFrame(rows)


def capacity_phase_in(capacity_change: float, years_since_change: int, phase_years: int = 15) -> float:
    """Odd (increase/cut symmetric) log-capacity effect with linear phase-in."""
    if capacity_change <= -1:
        raise ValueError("capacity cannot fall by 100% or more")
    if phase_years <= 0:
        raise ValueError("phase_years must be positive")
    signed_log = math.copysign(math.log1p(abs(float(capacity_change))), capacity_change)
    phase = min(1.0, max(0.0, float(years_since_change) / phase_years))
    return signed_log * phase


def _ramp(year: int, start: int = 2027, years: int = 4) -> float:
    return min(1.0, max(0.0, (year - start + 1) / years))


def _interpolate_population(population: pd.DataFrame, years: Sequence[int]) -> pd.DataFrame:
    pop = population.loc[population["sex"].eq("Ambos"), ["year", "age", "population"]].copy()
    return pop.loc[pop["year"].isin(years)]


def c5_schooling_channel(
    years: Sequence[int], population: pd.DataFrame, spending_change: Sequence[float], parameters: Mapping
) -> tuple[np.ndarray, np.ndarray]:
    """Call C5 schooling logic with an odd signed-log dose transformation."""
    frame = pd.DataFrame({"year": years, "scenario": "ED"})
    education_share = float(parameters["baseline"]["education_gdp_share"]["central"])
    spending = pd.Series(
        symmetric_c5_spending_change(np.asarray(spending_change, dtype=float), education_share),
        index=frame.index,
    )
    returns = parameters["long_run_feedback"]["human_capital_from_schooling"]["returns_per_year_of_schooling"]
    human, schooling = schooling_log_output_effect(
        frame, population, spending,
        base_adult_schooling_years=10.4,
        schooling_elasticity=float(parameters["social_outcome_elasticities"]["schooling_years_wrt_local_public_spending"]["central"]),
        education_share_gdp=education_share,
        capital_share=macro_input(parameters, "capital_share", "central"),
        return_up_to_4=float(returns["up_to_4_years"]),
        return_4_to_8=float(returns["years_4_to_8"]),
        return_above_8=float(returns["above_8_years"]),
    )
    return human.to_numpy(), schooling.to_numpy()


def symmetric_c5_spending_change(change: float | np.ndarray, education_share: float):
    """Map equal signed pp-GDP doses to equal/opposite C5 log spending doses."""
    values = np.asarray(change, dtype=float)
    if education_share <= 0:
        raise ValueError("education_share must be positive")
    log_dose = np.sign(values) * np.log1p(np.abs(values) / education_share)
    result = education_share * np.expm1(log_dose)
    return float(result) if result.ndim == 0 else result


def _young_schooling_path(
    years: Sequence[int], spending_change: Sequence[float], education_share: float,
    base_schooling: float, elasticity: float,
) -> np.ndarray:
    """C5 exposure arithmetic for the 18-24 indicator (adult output still uses C5)."""
    base_year = min(years)
    gains: dict[int, float] = {}
    result = []
    symmetric = symmetric_c5_spending_change(np.asarray(spending_change), education_share)
    for year, change in zip(years, symmetric):
        if year > base_year:
            annual = base_schooling * elasticity * math.log1p(change / education_share) / 12
            for age in range(6, 18):
                birth = year - age
                gains[birth] = gains.get(birth, 0.0) + annual
        result.append(float(np.mean([gains.get(year - age, 0.0) for age in range(18, 25)])))
    return np.asarray(result)


def _pe_paths(
    years: Sequence[int], population: pd.DataFrame, dropout_effect_pp: float,
    beneficiaries_mn: float, school_years: float,
) -> tuple[np.ndarray, np.ndarray]:
    pop = population.set_index(["year", "age"])["population"]
    cohort_gain: dict[int, float] = {}
    adult, young = [], []
    for year in years:
        eligible = sum(float(pop.get((year, age), 0.0)) for age in range(15, 18))
        share = min(1.0, beneficiaries_mn * 1e6 / eligible) if eligible else 0.0
        cohort_gain[year - 17] = abs(dropout_effect_pp) / 100 * share * school_years
        adults = population.loc[population["year"].eq(year) & population["age"].ge(25)]
        adult_gain = adults["age"].map(lambda age: cohort_gain.get(year - int(age), 0.0))
        adult.append(float(np.average(adult_gain, weights=adults["population"])))
        young.append(float(np.mean([cohort_gain.get(year - age, 0.0) for age in range(18, 25)])))
    return np.asarray(adult), np.asarray(young)


def _latest_baselines(parts: Mapping[str, pd.DataFrame]) -> dict[str, float | dict[str, float]]:
    years, dist, rates = parts["years"], parts["distribution"], parts["entrepreneurship"]
    adult = float(years.loc[
        years["geography"].eq("Brasil") & years["age_group"].eq("15 anos ou mais") & years["year"].eq(2025), "value"
    ].iloc[0])
    tertiary = float(dist.loc[
        dist["geography"].eq("Brasil") & dist["level"].eq("higher_complete") & dist["year"].eq(2025), "value"
    ].iloc[0])
    br = rates.loc[rates["geography"].eq("Brasil") & rates["year"].between(2012, 2025)]
    latest = br.loc[br["year"].eq(br["year"].max())]
    employer = float(latest.loc[latest["level"].eq("total"), "employer_rate_pct"].iloc[0])
    by_level = br.loc[~br["level"].eq("total")]
    fixed_emp = by_level.groupby("level")["employer_rate_pct"].mean().to_dict()
    fixed_cnpj = by_level.groupby("level")["cnpj_employer_rate_pct"].mean().to_dict()
    return {"adult": adult, "tertiary": tertiary, "employer": employer,
            "fixed_emp": fixed_emp, "fixed_cnpj": fixed_cnpj}


def _tertiary_response(parts: Mapping[str, pd.DataFrame]) -> float:
    years = parts["years"]
    dist = parts["distribution"]
    x = years.loc[years["geography"].eq("Brasil") & years["age_group"].eq("18 a 29 anos"), ["year", "value"]]
    y = dist.loc[dist["geography"].eq("Brasil") & dist["level"].eq("higher_complete"), ["year", "value"]]
    joined = x.merge(y, on="year", suffixes=("_years", "_tertiary"))
    return float(np.polyfit(joined["value_years"], joined["value_tertiary"], 1)[0])


def _programme_definitions(parameters: Mapping) -> dict[str, dict]:
    """Build the central P1 package paths on the same annual S0 used by C5."""
    population = pd.read_csv(ROOT / "data/brazil/population.csv")
    annual = project_baseline(
        pd.read_csv(ROOT / "data/brazil/fiscal.csv"),
        population,
        pd.read_csv(ROOT / "data/brazil/age_profiles.csv"),
        parameters,
        range(1, 36),
    )
    programme_config = yaml.safe_load(
        (ROOT / "config/programs_2026.yaml").read_text(encoding="utf-8")
    )
    s0 = programs.s0_path(annual, population, parameters)
    draw = programs.central_programme_draw(programme_config, parameters)
    return programs.build_programme_scenarios(s0, programme_config, draw)


def _package_path(definition: Mapping, package: str, years: Sequence[int], base_year: int) -> np.ndarray:
    """Read a P1 package gap (positive means spending below S0), holding its last value."""
    path = {int(k): float(v) for k, v in definition["package_gaps_by_year"].get(package, {}).items()}
    if not path:
        return np.zeros(len(years))
    last_horizon = max(path)
    return np.asarray([path.get(min(int(year) - base_year, last_horizon), 0.0) for year in years])


def programme_spending_changes(
    definition: Mapping, years: Sequence[int], variant: str, parameters: Mapping,
    rd_baseline_pp_gdp: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Education and R&D spending changes versus S0 implied by a P1 package path.

    This follows C5's central case for education: the services-package gap is split by
    the COFOG education/health shares and multiplied by the configured central fraction
    that removes services rather than efficiency.  MCTI R&D receives the same
    proportional change; this prevents an education package from affecting the
    capacity channel while silently bypassing the innovation channel.
    """
    # Spending paths are scenario inputs, not response-parameter outcomes.  Use
    # C5's central allocation once so low/central/high vary elasticities rather
    # than silently changing the fiscal counterfactual.
    education_share = float(parameters["baseline"]["education_gdp_share"]["central"])
    health_share = float(parameters["baseline"]["health_gdp_share"]["central"])
    allocation = education_share / (education_share + health_share)
    service_fraction = float(
        parameters["social_modelling_choices"]["reduction_hitting_health_education"]
        ["service_cut_fraction"]["central"]
    )
    service_gap = _package_path(
        definition, "efficiency_health_education_admin", years, min(years)
    )
    education = -service_gap * allocation * service_fraction
    rd = education / education_share * rd_baseline_pp_gdp
    return education, rd


def build_scenarios(
    config: Mapping, parts: Mapping[str, pd.DataFrame], estimates: pd.DataFrame,
) -> pd.DataFrame:
    years = np.arange(int(config["base_year"]), int(config["end_year"]) + 1)
    population_all = pd.read_csv(ROOT / "data/brazil/population.csv")
    population = _interpolate_population(population_all, years)
    parameters = load_macro_inputs(ROOT / "config/parameters.yaml")
    gdp = baseline_real_gdp_path(population_all, int(years[0]), int(years[-1]), parameters, "central")
    real_gdp = gdp.set_index("year")["real_gdp"]  # R$ million at the model's 2025 price anchor
    revenue_share = macro_input(parameters, "revenue_gdp", "central") / 100
    cofog = read_cofog_real()
    masks = spending_masks(cofog)
    cal = calibration_table(cofog).set_index("item")
    university_2024 = float(cal.loc["federal_universities_total", "r_bn_2024"])
    if_2024 = float(cal.loc["federal_institutes_total", "r_bn_2024"])
    mcti_2024 = float(cal.loc["mcti_budget_units", "r_bn_2024"])
    historical_uni = float(cal.loc["federal_universities_total", "change_2018_2022_pct"]) / 100
    historical_mcti = float(cal.loc["mcti_budget_units", "change_2018_2022_pct"]) / 100
    recomposition_uni = float(cal.loc["federal_universities_total", "change_2022_2024_pct"]) / 100
    recomposition_mcti = float(cal.loc["mcti_budget_units", "change_2022_2024_pct"]) / 100
    p = config["parameters"]
    baseline = _latest_baselines(parts)
    tertiary_slope = _tertiary_response(parts)
    crime_estimate = float(estimates.loc[estimates["analysis"].eq("crime_association"), "estimate"].iloc[0])
    definitions = _programme_definitions(parameters)
    gdp_bn = real_gdp.reindex(years).to_numpy() / 1000
    rd_baseline_pp = mcti_2024 / float(gdp_bn[0]) * 100
    rows: list[dict[str, object]] = []
    for scenario_name, scenario in config["scenarios"].items():
        definition = definitions[str(scenario["programme_scenario"])]
        for variant in VARIANTS:
            v = config["variants"][variant]
            package_education, package_rd = programme_spending_changes(
                definition, years, variant, parameters, rd_baseline_pp
            )
            human_log, c5_schooling = c5_schooling_channel(
                years, population, package_education, parameters
            )
            young_schooling = _young_schooling_path(
                years, package_education, float(parameters["baseline"]["education_gdp_share"]["central"]),
                float(baseline["adult"]),
                float(parameters["social_outcome_elasticities"]["schooling_years_wrt_local_public_spending"]["central"]),
            )
            total_schooling = c5_schooling
            young_total = young_schooling
            schooling_gdp = human_log * 100
            record_uni = recomposition_uni if scenario["programme"] == "lula_pt" else historical_uni
            record_mcti = recomposition_mcti if scenario["programme"] == "lula_pt" else historical_mcti
            uni_change = np.array([
                record_uni * float(scenario["university_record_fraction"]) * _ramp(int(year)) for year in years
            ])
            mcti_change = np.array([
                record_mcti * float(scenario["mcti_record_fraction"]) * _ramp(int(year)) for year in years
            ])
            university_pp = uni_change * university_2024 / gdp_bn * 100
            mcti_pp = mcti_change * mcti_2024 / gdp_bn * 100
            education_spending = package_education + university_pp
            rd_spending = package_rd + mcti_pp
            package_ratio = package_education / float(parameters["baseline"]["education_gdp_share"]["central"])
            capacity_change = (
                university_2024 * (uni_change + package_ratio)
                + if_2024 * package_ratio
            ) / (university_2024 + if_2024)
            capacity_log = np.array([
                capacity_phase_in(float(change), max(0, int(year) - 2026), int(p["capacity_phase_in_years"]))
                for year, change in zip(years, capacity_change)
            ])
            effectiveness = 1 + (float(v["applied_research_effectiveness"])
                                  if scenario["programme"] == "flavio_bolsonaro_pl" else 0.0)
            capacity_gdp = 100 * float(v["capacity_elasticity"]) * effectiveness * capacity_log
            investment_ratio = mcti_change + package_rd / rd_baseline_pp
            stock = 1.0
            innovation_log = []
            depreciation = float(p["rd_depreciation"])
            for change in investment_ratio:
                stock = (1 - depreciation) * stock + depreciation * (1 + change)
                innovation_log.append(math.copysign(math.log1p(abs(stock - 1)), stock - 1))
            innovation_gdp = 100 * float(v["innovation_elasticity"]) * np.asarray(innovation_log)
            tertiary_change = tertiary_slope * total_schooling
            fixed_emp = baseline["fixed_emp"]
            fixed_cnpj = baseline["fixed_cnpj"]
            employer_change = tertiary_change / 100 * (
                fixed_emp["higher_complete"] - fixed_emp["secondary_higher_incomplete"]
            )
            cnpj_change = tertiary_change / 100 * (
                fixed_cnpj["higher_complete"] - fixed_cnpj["secondary_higher_incomplete"]
            )
            if variant == "high":
                cnpj_change += float(p["cnpj_local_effect_pp_per_school_year"]) * total_schooling
            # Causal literature fixes the sign; the noisy panel magnitude is only an upper bound.
            homicide_change = -abs(crime_estimate) * young_total * float(v["homicide_association_fraction"])
            total_gdp = schooling_gdp + capacity_gdp + innovation_gdp
            education_spending_bn = education_spending / 100 * gdp_bn
            rd_spending_bn = rd_spending / 100 * gdp_bn
            fiscal_cost_bn = education_spending_bn + rd_spending_bn
            gdp_gain_bn = total_gdp / 100 * real_gdp.reindex(years).to_numpy() / 1000
            revenue_gain_bn = gdp_gain_bn * revenue_share
            discount = np.array([(1 + float(p["real_discount_rate"])) ** -(int(y) - int(years[0])) for y in years])
            for i, year in enumerate(years):
                rows.append({
                    "scenario": scenario_name, "variant": variant, "year": int(year),
                    "education_package_change_pp_gdp": package_education[i],
                    "education_spending_change_pp_gdp": education_spending[i],
                    "education_spending_change_r_bn_2025": education_spending_bn[i],
                    "rd_spending_change_pp_gdp": rd_spending[i],
                    "rd_spending_change_r_bn_2025": rd_spending_bn[i],
                    "university_budget_change_pct": uni_change[i] * 100,
                    "mcti_budget_change_pct": mcti_change[i] * 100,
                    "adult_mean_schooling_years": float(baseline["adult"]) + total_schooling[i],
                    "adult_mean_schooling_change_years": total_schooling[i],
                    "tertiary_share_25_34_proxy_pct": float(baseline["tertiary"]) + tertiary_change[i],
                    "capacity_index": 1 + capacity_change[i],
                    "schooling_gdp_level_effect_pct": schooling_gdp[i],
                    "capacity_gdp_level_effect_pct": capacity_gdp[i],
                    "innovation_gdp_level_effect_pct": innovation_gdp[i],
                    "total_gdp_level_effect_pct": total_gdp[i],
                    "employer_share_change_pp": employer_change[i],
                    "employer_share_pct": float(baseline["employer"]) + employer_change[i],
                    "cnpj_employer_share_change_pp": cnpj_change[i],
                    "youth_homicide_rate_change_per_100k_residents": homicide_change[i],
                    "fiscal_cost_r_bn_2025": fiscal_cost_bn[i],
                    "gdp_gain_r_bn_2025": gdp_gain_bn[i],
                    "revenue_gain_r_bn_2025": revenue_gain_bn[i],
                    "pv_fiscal_cost_to_date_r_bn_2025": float(np.sum(fiscal_cost_bn[:i + 1] * discount[:i + 1])),
                    "pv_gdp_gain_to_date_r_bn_2025": float(np.sum(gdp_gain_bn[:i + 1] * discount[:i + 1])),
                    "pv_revenue_gain_to_date_r_bn_2025": float(np.sum(revenue_gain_bn[:i + 1] * discount[:i + 1])),
                })
    return pd.DataFrame(rows)


def _md_table(frame: pd.DataFrame, decimals: int = 2) -> str:
    shown = frame.copy()
    for column in shown.select_dtypes(include=[np.number]):
        shown[column] = shown[column].map(lambda x: "" if pd.isna(x) else f"{x:.{decimals}f}")
    headers = list(shown.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None))
    return "\n".join(lines)


def write_reports(config: Mapping, estimates: pd.DataFrame, scenarios: pd.DataFrame) -> None:
    cal = calibration_table()
    selected = scenarios.loc[scenarios["year"].isin([2030, 2045, 2060]), [
        "scenario", "variant", "year", "schooling_gdp_level_effect_pct",
        "capacity_gdp_level_effect_pct", "innovation_gdp_level_effect_pct",
        "total_gdp_level_effect_pct", "employer_share_change_pp",
        "youth_homicide_rate_change_per_100k_residents",
    ]].rename(columns={"variant": "parameter_set"})
    pv = scenarios.loc[scenarios["year"].isin([2045, 2060]), [
        "scenario", "variant", "year", "pv_fiscal_cost_to_date_r_bn_2025",
        "pv_gdp_gain_to_date_r_bn_2025", "pv_revenue_gain_to_date_r_bn_2025",
    ]].rename(columns={"variant": "parameter_set"})
    spending = scenarios.loc[
        scenarios["variant"].eq("central") & scenarios["year"].isin([2027, 2030, 2045]),
        ["scenario", "year", "education_spending_change_pp_gdp",
         "education_spending_change_r_bn_2025", "rd_spending_change_pp_gdp",
         "rd_spending_change_r_bn_2025"],
    ]
    assumptions = pd.DataFrame(config["assumptions"])
    comp = estimates.loc[estimates["analysis"].eq("composition"), "estimate"].iloc[0]
    crime = estimates.loc[estimates["analysis"].eq("crime_association")].iloc[0]
    report = f"""# Education measures and scenarios

This deterministic module applies identical rules to spending increases and cuts. It does not assess candidates' merits and is not yet wired into Monte Carlo. Historical-record/recomposition cases are labelled sensitivities, not statements in either programme; the Flávio governance proposal contains no budget number.

S0 is the no-policy-change reference. Pé-de-Meia, the PBIA through 2028, the 100 IF campi already under construction, and current university/MCTI budgets are in S0, so they contribute **zero** incremental cost and effect in every current-law case. No programme states PBIA spending beyond 2028, and no unsupported IF operating increment is added. Differences come only from each P1 package path and the explicitly labelled historical-record sensitivities.

## Recomputed spending calibration

All amounts are R$ billion in average-2024 prices (monthly IPCA compounded to an annual-average index). The university rule excludes university hospitals; the IF rule includes compact `INST.FED` names, CEFET variants and Colégio Pedro II.

{_md_table(cal)}

## Descriptive estimates

The 2016-2025 attainment composition shift implies an employer-rate change of **{comp:.3f} pp** at fixed 2012-2025 education-specific rates. This is descriptive. The state-and-year fixed-effects association is **{crime['estimate']:.3f}** youth homicides per 100,000 residents per additional mean school year among ages 18-24 (clustered SE {crime['std_error']:.3f}, {int(crime['clusters'])} states); it is not causal. Bergmann's local-campus employer-rate result is statistically zero, so the default local effect is zero.

## Assumptions (all judgment-based numbers)

{_md_table(assumptions)}

Source-based fixed numbers and their citations are listed in `config/ed_proposed.yaml` under `source_parameters`; they are not assumptions. Pé-de-Meia's -6.5 pp is an ex-ante simulation, not an observed causal estimate; it is not an incremental scenario effect because the programme already exists in S0. The COFOG extract does not separately identify Pé-de-Meia, so the historical panel leaves that line missing rather than inventing a value.

## GDP-level and indicator results

Log-percentage-point GDP level effects are relative to S0 and split into schooling, higher-education capacity and public-R&D stock channels. Employer share and youth homicide are indicators, not additional GDP channels. The 25-34 tertiary level is explicitly a proxy anchored to the observed 14+ series because the archived SIDRA table has no 25-34 cross-tab.

Low/central/high are **response-parameter sets**, not ordered outcome bounds; the fiscal spending path is identical across them. In spending-cut scenarios, the low set assigns zero output elasticity and can therefore produce a numerically larger GDP outcome than the high set; the labels must not be read as min/median/max.

{_md_table(selected, 3)}

## Present-value comparison

Costs/savings and GDP/revenue changes use the common C2 real-GDP path, a 3% real discount rate, and the observed model revenue/GDP ratio. Negative fiscal cost is a saving; negative GDP gain is a loss. The 2060 column is the separately reported post-2045 tail-inclusive total.

{_md_table(pv, 1)}

## Spending changes that drive the channels

Positive values are spending above S0 (fiscal costs); negative values are spending below S0 (savings). Spending paths are identical across response-parameter sets, so each scenario appears once. Education follows C5's central P1 services-package allocation; public R&D receives the same proportional package change, plus any labelled MCTI historical-record sensitivity.

{_md_table(spending, 3)}
"""
    method = """# ED method

`python -m src.education` reads only archived inputs and rebuilds the panel, estimates, scenario paths, and this documentation. SIDRA JSON is parsed by classification and geography. Entrepreneur rates divide each quarterly numerator by occupied people in the matching harmonised education group, then average quarterly rates within year. Composition holds the 2012-2025 national education-specific rates fixed.

The crime regression uses 2016-2019 and 2022-2024 state observations, state and year fixed effects, and state-clustered standard errors. The available youth series is a count, so it is converted to youth homicides per 100,000 total residents using the total homicide count and total-resident rate. This denominator is disclosed everywhere.

COFOG 2024 source observations are in R$ million; the archived `value_brl` field has already multiplied them by one million. `rescale_2024_source_units` tests the source conversion and the production reader prevents a second conversion. Nominal flows are deflated with the annual mean of the compounded monthly IPCA index.

Schooling imports and calls `src.feedback.schooling_log_output_effect`; an odd signed-log dose maps equal-sized increases and cuts to exact opposites before that call. Capacity is proportional to real university and IF capacity, and its signed log change phases in over 15 years. Channel results are reported as additive log-percentage-point level effects, preserving exact symmetry. Public R&D uses a 15% depreciation perpetual-inventory stock. Capacity and innovation elasticities are 0/0.02/0.04 and 0/0.01/0.02. Low/central/high identify these parameter sets, not ordered outcomes. No entrepreneurship or crime indicator is fed back into GDP.

The five programme paths are built by `src.programs.build_programme_scenarios` on the annual C1 S0 path, with the central P1 draw. Education follows C5's central case: the scenario's own `efficiency_health_education_admin` package gap is allocated between health and education by their COFOG shares and multiplied by the central service-loss fraction. The resulting fiscal path is held fixed across low/central/high response-parameter sets. Public R&D receives the same proportional package change. Pé-de-Meia, PBIA through 2028, the 100 IF campi under construction, and current university/MCTI budgets are already in S0 and therefore add zero incremental cost or effect. Historical-repeat/recomposition university and MCTI paths ramp over 2027-2030 and are held thereafter. All judgment-based numerical assumptions, with a basis, are in `config/ed_proposed.yaml`; source-derived fixed numbers are separated under `source_parameters`.
"""
    PATHS["report"].write_text(report, encoding="utf-8")
    PATHS["docs"].write_text(method, encoding="utf-8")


def main() -> None:
    config = yaml.safe_load(PATHS["config"].read_text(encoding="utf-8"))
    panel, parts = build_panel()
    estimates = build_estimates(parts)
    scenarios = build_scenarios(config, parts, estimates)
    panel.to_csv(PATHS["panel"], index=False)
    estimates.to_csv(PATHS["estimates"], index=False)
    scenarios.to_csv(PATHS["scenarios"], index=False)
    write_reports(config, estimates, scenarios)
    print(f"wrote {len(panel)} panel rows, {len(estimates)} estimates, {len(scenarios)} scenario rows")


if __name__ == "__main__":
    main()
