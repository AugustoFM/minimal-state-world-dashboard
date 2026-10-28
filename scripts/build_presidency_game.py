"""Build the deterministic offline transition library for the presidency game."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.presidency_game import INDICATORS, PRIMARY_ACTIONS, PresidencyGameAdapter, validate_action_mappings


CANDIDATES = ("Lula", "Flavio")
INTEGRITY_VARIANTS = ("current_controls", "integrity_sensitivity")
PERCENTILES = (10, 50, 90)


def _path_key(sequence: tuple[str, ...]) -> str:
    return "+".join(sequence)


def build(draws: int, seed: int) -> dict:
    validate_action_mappings()
    adapter = PresidencyGameAdapter()
    sequences_by_candidate = {
        candidate: list(itertools.product(PRIMARY_ACTIONS[candidate], repeat=4))
        for candidate in CANDIDATES
    }
    samples: dict[tuple[str, str], list] = {}
    work = [
        (candidate, sequence, draw_number)
        for candidate in CANDIDATES
        for sequence in sequences_by_candidate[candidate]
        for draw_number in range(draws)
    ]
    def evaluate(item):
        candidate, sequence, draw_number = item
        draw = adapter.draw(seed + draw_number, draw_number)
        frames = [
            adapter.run_path(candidate, sequence, integrity=integrity, draw=draw)
            for integrity in INTEGRITY_VARIANTS
        ]
        return candidate, _path_key(sequence), frames
    with ThreadPoolExecutor(max_workers=16) as pool:
        for candidate, key, frames in pool.map(evaluate, work):
            for integrity, frame in zip(INTEGRITY_VARIANTS, frames):
                samples.setdefault((candidate, integrity, key), []).append(frame)

    paths = {}
    for candidate in CANDIDATES:
        paths[candidate] = {}
        for integrity in INTEGRITY_VARIANTS:
            paths[candidate][integrity] = {}
            for sequence in sequences_by_candidate[candidate]:
                key = _path_key(sequence)
                frames = samples[candidate, integrity, key]
                by_percentile = {}
                for percentile in PERCENTILES:
                    rounds = []
                    for round_number in range(1, 5):
                        row = {"round": round_number, "year": adapter.base_year + round_number}
                        for output_name, (_, column) in INDICATORS.items():
                            values = np.array([float(frame.loc[frame["round"].eq(round_number), column].iloc[0]) for frame in frames])
                            row[output_name] = float(np.percentile(values, percentile, method="linear"))
                        rounds.append(row)
                    # A composite score would require arbitrary weights across
                    # unlike units; preserve the required field without inventing
                    # an economic coefficient or pretending it is model output.
                    by_percentile[str(percentile)] = {"rounds": rounds, "final_score": None}
                paths[candidate][integrity][key] = by_percentile

    return {
        "schema_version": 2,
        "base_year": adapter.base_year,
        "years": [adapter.base_year + i for i in range(1, 5)],
        "indicators": {name: {"unit": unit, "source_column": column} for name, (unit, column) in INDICATORS.items()},
        "actions": {
            "primary": {candidate: list(PRIMARY_ACTIONS[candidate]) for candidate in CANDIDATES},
            "integrity": list(INTEGRITY_VARIANTS),
        },
        "paths": paths,
        "metadata": {
            "seed": seed,
            "draw_count": draws,
            "model_variant": "central macro corner, transitory persistence; C2 -> C4 -> C3",
            "integrity_caveat": "Integrity sensitivity uses existing W3 leakage ranges; it has no quantified candidate-promise basis and is not an estimate.",
            "path_schema": "paths[candidate][integrity_choice][action_sequence][percentile]",
            "integrity_variants_in_library": list(INTEGRITY_VARIANTS),
            "action_to_parameter_mappings": "config/presidency_game.yaml",
            "action_definitions": {
                candidate: {
                    action: {key: definition[key] for key in ("label", "description", "source_items")}
                    for action, definition in definitions.items()
                }
                for candidate, definitions in adapter.game_config["primary_actions"].items()
            },
            "units": {name: unit for name, (unit, _) in INDICATORS.items()},
            "generated_date": date.today().isoformat(),
            "approx_live_births_by_year": adapter.approx_live_births_by_year,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261028)
    parser.add_argument("--output", default="presidency-game/game_data.json")
    args = parser.parse_args()
    if args.draws < 3:
        raise SystemExit("--draws must be at least 3 for p10/p50/p90")
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    data = build(args.draws, args.seed)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(CANDIDATES) * 4 ** 4} primary paths, {args.draws} draws -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
