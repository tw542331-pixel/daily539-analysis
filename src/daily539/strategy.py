from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from itertools import combinations
from math import sqrt
from statistics import mean, pstdev

from .analysis import snapshot, sum_interval
from .models import Draw


EXPECTED_NUMBER_RATE = 5 / 39


@dataclass(frozen=True)
class StrategyConfig:
    weight_10: float = 0.35
    weight_30: float = 0.45
    weight_100: float = 0.65
    weight_5y: float = 0.25
    missing_weight: float = 0.15
    pair_weight: float = 0.15
    sum_weight: float = 0.15
    tail_weight: float = 0.10
    repeat_weight: float = 0.25


DEFAULT_CONFIG = StrategyConfig()


def valid_combo(combo: tuple[int, ...], interval: tuple[int, int]) -> bool:
    odds = sum(n % 2 for n in combo)
    small = sum(n <= 19 for n in combo)
    gaps = [b - a for a, b in zip(combo, combo[1:])]
    decades = max(sum(a <= n <= b for n in combo) for a, b in ((1, 9), (10, 19), (20, 29), (30, 39)))
    return (odds in (2, 3) and small in (2, 3) and interval[0] <= sum(combo) <= interval[1]
            and not all(gap == 1 for gap in gaps) and decades <= 3)


def _window_draws(draws: list[Draw]) -> dict[str, list[Draw]]:
    cutoff = draws[-1].date - timedelta(days=365 * 5 + 2)
    return {
        "10": draws[-10:],
        "30": draws[-30:],
        "100": draws[-100:],
        "5y": [draw for draw in draws if draw.date >= cutoff],
    }


def number_scores(draws: list[Draw], config: StrategyConfig = DEFAULT_CONFIG) -> dict[int, float]:
    """Return comparable number signals; scores are rankings, not probabilities."""
    if not draws:
        raise ValueError("selection requires historical draws")
    samples = _window_draws(draws)
    frequencies = {
        label: Counter(number for draw in sample for number in draw.numbers)
        for label, sample in samples.items()
    }
    weights = {
        "10": config.weight_10,
        "30": config.weight_30,
        "100": config.weight_100,
        "5y": config.weight_5y,
    }
    missing = snapshot(draws[-100:])["missing"]
    scores: dict[int, float] = {}
    for number in range(1, 40):
        score = 0.0
        for label, sample in samples.items():
            size = len(sample)
            if not size:
                continue
            expected = size * EXPECTED_NUMBER_RATE
            deviation = sqrt(size * EXPECTED_NUMBER_RATE * (1 - EXPECTED_NUMBER_RATE))
            z_score = (frequencies[label][number] - expected) / deviation
            score += weights[label] * max(-3.0, min(3.0, z_score))

        score += config.missing_weight * min(missing[number], 15) / 15
        scores[number] = score
    return scores


def _factor_context(draws: list[Draw], scores: dict[int, float], config: StrategyConfig) -> dict:
    recent = draws[-100:]
    pair_counts = Counter(pair for draw in recent for pair in combinations(draw.numbers, 2))
    pair_expected = len(recent) * 10 / 741
    sums = [sum(draw.numbers) for draw in recent]
    return {
        "scores": scores,
        "pairs": pair_counts,
        "pair_expected": pair_expected,
        "sum_mean": mean(sums),
        "sum_deviation": pstdev(sums) or 1,
        "latest": set(draws[-1].numbers),
        "config": config,
    }


def _combo_factors(combo: tuple[int, ...], context: dict) -> dict[str, float]:
    config = context["config"]
    pair_average = sum(context["pairs"][pair] for pair in combinations(combo, 2)) / 10
    pair_signal = config.pair_weight * (pair_average - context["pair_expected"]) / sqrt(context["pair_expected"])
    sum_signal = -config.sum_weight * abs(sum(combo) - context["sum_mean"]) / context["sum_deviation"]
    tail_signal = config.tail_weight * (len({number % 10 for number in combo}) - 3)
    repeated = len(set(combo) & context["latest"])
    repeat_signal = -config.repeat_weight * max(0, repeated - 1)
    number_signal = sum(context["scores"][number] for number in combo)
    return {
        "number": number_signal,
        "pair": pair_signal,
        "sum": sum_signal,
        "tail": tail_signal,
        "repeat": repeat_signal,
        "total": number_signal + pair_signal + sum_signal + tail_signal + repeat_signal,
    }


def combo_factors(draws: list[Draw], combo: tuple[int, ...],
                  scores: dict[int, float] | None = None,
                  config: StrategyConfig = DEFAULT_CONFIG) -> dict[str, float]:
    """Break a combination score into reportable, auditable factors."""
    scores = scores or number_scores(draws, config)
    return _combo_factors(combo, _factor_context(draws, scores, config))


def select(draws: list[Draw], count: int = 2, seed: int | None = None,
           config: StrategyConfig = DEFAULT_CONFIG) -> list[tuple[int, ...]]:
    """Select deterministic, diversified candidates from a multi-factor rank."""
    del seed  # Kept for CLI/API compatibility; the model has no random tie-breaking.
    if not draws:
        raise ValueError("selection requires historical draws")
    scores = number_scores(draws, config)
    context = _factor_context(draws, scores, config)
    ranked = sorted(range(1, 40), key=lambda number: (-scores[number], number))

    interval = (45, 155)
    for pool_size in (18, 24, 39):
        candidates: list[tuple[float, tuple[int, ...]]] = []
        for values in combinations(ranked[:pool_size], 5):
            combo = tuple(sorted(values))
            if valid_combo(combo, interval):
                candidates.append((_combo_factors(combo, context)["total"], combo))
        candidates.sort(key=lambda item: (-item[0], item[1]))

        selected: list[tuple[int, ...]] = []
        for _, combo in candidates:
            if all(not (set(combo) & set(previous)) for previous in selected):
                selected.append(combo)
            if len(selected) == count:
                return selected
        for _, combo in candidates:
            if combo not in selected and all(len(set(combo) & set(previous)) <= 1 for previous in selected):
                selected.append(combo)
            if len(selected) == count:
                return selected
    raise ValueError("selection constraints produced too few combinations")


def select_legacy(draws: list[Draw], count: int = 2,
                  seed: int | None = None) -> list[tuple[int, ...]]:
    """Preserve the previous strategy so backtests can compare like-for-like."""
    if not draws:
        raise ValueError("selection requires historical draws")
    stats = snapshot(draws[-100:])
    interval = sum_interval(draws)
    rng = random.Random(seed)
    scores = {
        number: stats["frequencies"][number] + min(stats["missing"][number], 10) / 4
        for number in range(1, 40)
    }
    tie_breaks = {number: rng.random() for number in range(1, 40)}
    ranked = sorted(range(1, 40), key=lambda number: (scores[number], tie_breaks[number]), reverse=True)
    for pool_size in (16, 24, 39):
        candidates = [
            tuple(sorted(values))
            for values in combinations(ranked[:pool_size], 5)
            if valid_combo(tuple(sorted(values)), interval)
        ]
        rng.shuffle(candidates)
        candidates.sort(key=lambda combo: sum(scores[number] for number in combo), reverse=True)
        selected: list[tuple[int, ...]] = []
        for combo in candidates:
            if all(len(set(combo) & set(previous)) <= 2 for previous in selected):
                selected.append(combo)
            if len(selected) == count:
                return selected
    raise ValueError("selection constraints produced too few combinations")
