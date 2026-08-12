from __future__ import annotations

import random
from itertools import combinations

from .analysis import snapshot, sum_interval
from .models import Draw


def valid_combo(combo: tuple[int, ...], interval: tuple[int, int]) -> bool:
    odds = sum(n % 2 for n in combo)
    small = sum(n <= 19 for n in combo)
    gaps = [b - a for a, b in zip(combo, combo[1:])]
    decades = max(sum(a <= n <= b for n in combo) for a, b in ((1, 9), (10, 19), (20, 29), (30, 39)))
    return (odds in (2, 3) and small in (2, 3) and interval[0] <= sum(combo) <= interval[1]
            and not all(gap == 1 for gap in gaps) and decades <= 3)


def select(draws: list[Draw], count: int = 2, seed: int | None = None) -> list[tuple[int, ...]]:
    if not draws:
        raise ValueError("selection requires historical draws")
    stats = snapshot(draws[-100:])
    interval = sum_interval(draws)
    rng = random.Random(seed)
    scores = {n: stats["frequencies"][n] + min(stats["missing"][n], 10) / 4 for n in range(1, 40)}

    # The previous implementation rebuilt and sorted all C(39, 5) = 575,757
    # combinations for every historical draw in a backtest. Rank the numbers
    # first and search a compact pool; expand only if the constraints cannot
    # produce enough distinct picks.
    tie_breaks = {n: rng.random() for n in range(1, 40)}
    ranked = sorted(range(1, 40), key=lambda n: (scores[n], tie_breaks[n]), reverse=True)
    for pool_size in (16, 24, 39):
        candidates = []
        for values in combinations(ranked[:pool_size], 5):
            combo = tuple(sorted(values))
            if valid_combo(combo, interval):
                candidates.append(combo)
        rng.shuffle(candidates)
        candidates.sort(key=lambda combo: sum(scores[n] for n in combo), reverse=True)
        selected: list[tuple[int, ...]] = []
        for combo in candidates:
            if all(len(set(combo) & set(previous)) <= 2 for previous in selected):
                selected.append(combo)
            if len(selected) == count:
                return selected
    raise ValueError("selection constraints produced too few combinations")
