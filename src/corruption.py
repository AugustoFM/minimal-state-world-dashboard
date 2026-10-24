"""Corruption-scandal GDP level paths for the Brazil Monte Carlo.

The functions in this module are pure apart from reading the proposed YAML
configuration.  A caller owns and passes the NumPy random generator, allowing
one event path to be drawn once and shared by every scenario in that draw.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a corruption configuration from ``path``."""
    with Path(path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Corruption configuration must be a mapping")
    return config


def sample_events(
    rng: np.random.Generator, years: int, probability: float
) -> np.ndarray:
    """Draw independent annual scandal-event indicators."""
    if years < 0:
        raise ValueError("years must be non-negative")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between zero and one")
    return rng.random(years) < probability


def sample_magnitudes(
    rng: np.random.Generator, n: int, low: float, mode: float, high: float
) -> np.ndarray:
    """Draw ``n`` positive GDP loss magnitudes in percentage points."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if not 0.0 <= low <= mode <= high:
        raise ValueError("magnitude bounds must satisfy 0 <= low <= mode <= high")
    return rng.triangular(low, mode, high, size=n)


def level_path(
    event_steps: np.ndarray,
    magnitudes: np.ndarray,
    years: int,
    build_up_years: int,
    half_life_years: float,
) -> np.ndarray:
    """Return the aggregate GDP log-level deviation, in percent.

    An event is felt in its event year, reaches its full magnitude in the last
    build-up year, and subsequently decays exponentially.  Contributions from
    overlapping events add in log-level percentage terms.
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    if build_up_years < 1:
        raise ValueError("build_up_years must be at least one")
    if half_life_years <= 0:
        raise ValueError("half_life_years must be positive")

    events = np.asarray(event_steps, dtype=bool)
    losses = np.asarray(magnitudes, dtype=float)
    if events.ndim != 1 or len(events) != years:
        raise ValueError("event_steps must be a one-dimensional array of length years")
    if losses.ndim != 1 or len(losses) != int(events.sum()):
        raise ValueError("magnitudes must contain one value per event")
    if np.any(losses < 0) or not np.all(np.isfinite(losses)):
        raise ValueError("magnitudes must be finite and non-negative")

    path = np.zeros(years, dtype=float)
    for event_index, magnitude in zip(np.flatnonzero(events), losses):
        elapsed = np.arange(years - event_index)
        contribution = np.empty_like(elapsed, dtype=float)
        building = elapsed < build_up_years
        contribution[building] = -magnitude * (elapsed[building] + 1) / build_up_years
        contribution[~building] = -magnitude * 0.5 ** (
            (elapsed[~building] - (build_up_years - 1)) / half_life_years
        )
        path[event_index:] += contribution
    return path


def draw_path(
    rng: np.random.Generator, years: int, config: Mapping[str, Any]
) -> pd.DataFrame:
    """Draw one event sequence and its GDP log-level path."""
    probability_config = config["annual_probability"]
    probability = float(rng.uniform(probability_config["low"], probability_config["high"]))
    events = sample_events(rng, years, probability)
    magnitude_config = config["gdp_level_loss_pct"]
    magnitudes = sample_magnitudes(
        rng,
        int(events.sum()),
        float(magnitude_config["low"]),
        float(magnitude_config["mode"]),
        float(magnitude_config["high"]),
    )
    levels = level_path(
        events,
        magnitudes,
        years,
        int(config["build_up_years"]),
        float(config["recovery_half_life_years"]),
    )
    frame = pd.DataFrame(
        {
            "step": np.arange(1, years + 1, dtype=int),
            "corruption_event": events.astype(int),
            "corruption_event_magnitude_pct": np.where(events, np.nan, 0.0),
            "corruption_gdp_level_pct": levels,
        }
    )
    frame.loc[events, "corruption_event_magnitude_pct"] = magnitudes
    frame.attrs["sampled_probability"] = probability
    return frame


def thinned_path(
    shared_path: pd.DataFrame,
    reduction_fraction: float,
    event_uniforms: np.ndarray,
    config: Mapping[str, Any],
    first_eligible_step: int = 1,
) -> np.ndarray:
    """Return a scenario path after thinning the shared event sequence.

    The uniforms are drawn once per shared event and can therefore be reused
    for every enabled programme scenario without breaking pairing.
    """
    q = float(reduction_fraction)
    if not 0.0 <= q <= 1.0:
        raise ValueError("reduction_fraction must be between zero and one")
    required = {"corruption_event", "corruption_event_magnitude_pct"}
    if missing := required - set(shared_path.columns):
        raise ValueError(f"shared_path is missing columns: {sorted(missing)}")
    events = shared_path["corruption_event"].to_numpy(dtype=bool)
    magnitudes = shared_path.loc[events, "corruption_event_magnitude_pct"].to_numpy(dtype=float)
    uniforms = np.asarray(event_uniforms, dtype=float)
    if uniforms.ndim != 1 or len(uniforms) != len(magnitudes):
        raise ValueError("event_uniforms must contain one value per shared event")
    if np.any((uniforms < 0.0) | (uniforms >= 1.0)):
        raise ValueError("event_uniforms must lie in [0, 1)")
    if first_eligible_step < 1:
        raise ValueError("first_eligible_step must be at least one")
    event_steps = np.flatnonzero(events) + 1
    kept = (event_steps < first_eligible_step) | (uniforms >= q)
    thinned_events = np.zeros(len(events), dtype=bool)
    thinned_events[np.flatnonzero(events)[kept]] = True
    return level_path(
        thinned_events,
        magnitudes[kept],
        len(events),
        int(config["build_up_years"]),
        float(config["recovery_half_life_years"]),
    )


def central_path(years: int) -> pd.DataFrame:
    """Return the no-event central path used outside stochastic runs."""
    if years < 0:
        raise ValueError("years must be non-negative")
    return pd.DataFrame(
        {
            "step": np.arange(1, years + 1, dtype=int),
            "corruption_event": np.zeros(years, dtype=int),
            "corruption_gdp_level_pct": np.zeros(years, dtype=float),
        }
    )


def cpi_sensitivity_path(
    years: int, points: float, config: Mapping[str, Any]
) -> np.ndarray:
    """Illustrative GDP-per-capita level effect of a sustained CPI change.

    This function does not activate the sensitivity automatically.  ``points``
    is the CPI improvement relative to baseline (negative values represent a
    deterioration).
    """
    if years < 0:
        raise ValueError("years must be non-negative")
    sensitivity = config["cpi_sensitivity"]
    standard_deviation = float(sensitivity["cross_country_cpi_sd_points"])
    phase_in_years = int(sensitivity["phase_in_years"])
    if standard_deviation <= 0 or phase_in_years < 1:
        raise ValueError("CPI standard deviation and phase-in years must be positive")
    long_run_effect = (
        float(points)
        / standard_deviation
        * float(sensitivity["gdp_per_capita_level_effect_pct_per_sd"])
    )
    phase = np.minimum(np.arange(1, years + 1, dtype=float) / phase_in_years, 1.0)
    return long_run_effect * phase
