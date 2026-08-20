from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from math import sqrt

from .models import Draw
from .strategy import DEFAULT_CONFIG, number_scores, valid_combo


@dataclass(frozen=True)
class ThreeHitConfig:
    window: int = 100
    pool_size: int = 18
    triple_weight: float = 1.0
    number_weight: float = 0.35
    max_overlap: int = 0


def _triple_scores(draws: list[Draw], window: int) -> dict[tuple[int, int, int], float]:
    recent = draws[-window:]
    counts = Counter(
        triple
        for draw in recent
        for triple in combinations(draw.numbers, 3)
    )
    # A specific triple appears in a random 5/39 draw with probability C(36,2)/C(39,5).
    expected = len(recent) * 10 / 9139 if recent else 0.0
    deviation = sqrt(expected) if expected > 0 else 1.0
    return {
        triple: (counts[triple] - expected) / deviation
        for triple in combinations(range(1, 40), 3)
    }


def _combo_score(
    combo: tuple[int, ...],
    triples: dict[tuple[int, int, int], float],
    numbers: dict[int, float],
    config: ThreeHitConfig,
) -> float:
    triple_signal = sum(triples[triple] for triple in combinations(combo, 3))
    number_signal = sum(numbers[number] for number in combo)
    return config.triple_weight * triple_signal + config.number_weight * number_signal


def select_three_hit(
    draws: list[Draw],
    count: int = 2,
    seed: int | None = None,
    config: ThreeHitConfig = ThreeHitConfig(),
) -> list[tuple[int, ...]]:
    """Select tickets by directly ranking historical three-number structures."""
    del seed
    if not draws:
        raise ValueError("selection requires historical draws")
    if count < 1:
        raise ValueError("count must be positive")
    if config.window < 10:
        raise ValueError("window must be at least 10")
    if not 10 <= config.pool_size <= 39:
        raise ValueError("pool_size must be between 10 and 39")
    if not 0 <= config.max_overlap <= 2:
        raise ValueError("max_overlap must be between 0 and 2")

    numbers = number_scores(draws, DEFAULT_CONFIG)
    triples = _triple_scores(draws, config.window)
    ranked_numbers = sorted(range(1, 40), key=lambda n: (-numbers[n], n))
    interval = (45, 155)

    candidates: list[tuple[float, tuple[int, ...]]] = []
    for values in combinations(ranked_numbers[:config.pool_size], 5):
        combo = tuple(sorted(values))
        if valid_combo(combo, interval):
            candidates.append((_combo_score(combo, triples, numbers, config), combo))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    selected: list[tuple[int, ...]] = []
    for _, combo in candidates:
        if all(len(set(combo) & set(previous)) <= config.max_overlap for previous in selected):
            selected.append(combo)
        if len(selected) == count:
            return selected

    raise ValueError("three-hit constraints produced too few combinations")
