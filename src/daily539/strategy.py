from __future__ import annotations

import random
from collections import Counter
from datetime import timedelta
from itertools import combinations
from math import sqrt
from statistics import mean, pstdev

from .analysis import snapshot, sum_interval
from .models import Draw


EXPECTED_NUMBER_RATE = 5 / 39
WINDOW_WEIGHTS = {"10": 0.35, "30": 0.45, "100": 0.65, "5y": 0.25}


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


def number_scores(draws: list[Draw]) -> dict[int, float]:
    """Return comparable number signals; scores are rankings, not probabilities."""
    if not draws:
        raise ValueError("selection requires historical draws")
    samples = _window_draws(draws)
    frequencies = {
        label: Counter(number for draw in sample for number in draw.numbers)
        for label, sample in samples.items()
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
            score += WINDOW_WEIGHTS[label] * max(-3.0, min(3.0, z_score))

        # Keep omission visible without treating an overdue number as "due".
        score += 0.15 * min(missing[number], 15) / 15
        scores[number] = score
    return scores


def _factor_context(draws: list[Draw], scores: dict[int, float]) -> dict:
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
    }


def _combo_factors(combo: tuple[int, ...], context: dict) -> dict[str, float]:
    pair_average = sum(context["pairs"][pair] for pair in combinations(combo, 2)) / 10
    pair_signal = 0.15 * (pair_average - context["pair_expected"]) / sqrt(context["pair_expected"])
    sum_signal = -0.15 * abs(sum(combo) - context["sum_mean"]) / context["sum_deviation"]
    tail_signal = 0.10 * (len({number % 10 for number in combo}) - 3)
    repeated = len(set(combo) & context["latest"])
    repeat_signal = -0.25 * max(0, repeated - 1)
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
                  scores: dict[int, float] | None = None) -> dict[str, float]:
    """Break a combination score into reportable, auditable factors."""
    scores = scores or number_scores(draws)
    return _combo_factors(combo, _factor_context(draws, scores))


def select(draws: list[Draw], count: int = 2, seed: int | None = None) -> list[tuple[int, ...]]:
    """Select deterministic, diversified candidates from a multi-factor rank."""
    del seed  # Kept for CLI/API compatibility; the model has no random tie-breaking.
    if not draws:
        raise ValueError("selection requires historical draws")
    scores = number_scores(draws)
    context = _factor_context(draws, scores)
    ranked = sorted(range(1, 40), key=lambda number: (-scores[number], number))

    # Only reject historically extreme sums; relative quality is scored below.
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
