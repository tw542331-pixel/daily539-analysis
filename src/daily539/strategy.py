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
    candidates = [combo for combo in combinations(range(1, 40), 5) if valid_combo(combo, interval)]
    rng.shuffle(candidates)
    candidates.sort(key=lambda c: sum(stats["frequencies"][n] + min(stats["missing"][n], 10) / 4 for n in c), reverse=True)
    selected: list[tuple[int, ...]] = []
    for combo in candidates:
        if not selected or len(set(combo) & set(selected[0])) <= 2:
            selected.append(combo)
        if len(selected) == count:
            break
    return selected

