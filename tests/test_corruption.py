from __future__ import annotations

import numpy as np
import pytest

from src import corruption


CONFIG = corruption.load_config("config/corruption_proposed.yaml")


def test_zero_probability_gives_zero_path() -> None:
    rng = np.random.default_rng(11)
    events = corruption.sample_events(rng, 20, 0.0)
    path = corruption.level_path(events, np.array([]), 20, 2, 4)
    assert not events.any()
    np.testing.assert_array_equal(path, np.zeros(20))


def test_single_event_builds_and_half_recovers() -> None:
    events = np.array([True] + [False] * 9)
    magnitude = 2.4
    path = corruption.level_path(events, np.array([magnitude]), 10, 2, 4)
    assert path[1] == pytest.approx(-magnitude)
    assert path[5] == pytest.approx(-magnitude / 2)


def test_overlapping_event_effects_add() -> None:
    first = np.array([True, False, False, False, False])
    second = np.array([False, True, False, False, False])
    both = first | second
    first_path = corruption.level_path(first, np.array([2.0]), 5, 2, 4)
    second_path = corruption.level_path(second, np.array([3.0]), 5, 2, 4)
    combined = corruption.level_path(both, np.array([2.0, 3.0]), 5, 2, 4)
    np.testing.assert_allclose(combined, first_path + second_path)


def test_sampling_is_deterministic_for_seed() -> None:
    first = corruption.draw_path(np.random.default_rng(20261021), 20, CONFIG)
    second = corruption.draw_path(np.random.default_rng(20261021), 20, CONFIG)
    assert first.equals(second)
    assert first.attrs == second.attrs


def test_expected_event_count_is_close_to_binomial_mean() -> None:
    rng = np.random.default_rng(7)
    probability = 0.06
    counts = [corruption.sample_events(rng, 20, probability).sum() for _ in range(20_000)]
    assert np.mean(counts) == pytest.approx(20 * probability, abs=0.03)


def test_sampled_probability_respects_bounds() -> None:
    for seed in range(500):
        frame = corruption.draw_path(np.random.default_rng(seed), 20, CONFIG)
        probability = frame.attrs["sampled_probability"]
        assert CONFIG["annual_probability"]["low"] <= probability <= CONFIG["annual_probability"]["high"]
