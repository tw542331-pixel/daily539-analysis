from __future__ import annotations

from collections import Counter
from datetime import timedelta
from itertools import combinations
from statistics import quantiles

from .models import Draw


def snapshot(draws: list[Draw]) -> dict:
    frequencies = Counter(n for draw in draws for n in draw.numbers)
    tails = Counter(n % 10 for draw in draws for n in draw.numbers)
    pairs = Counter(pair for draw in draws for pair in combinations(draw.numbers, 2))
    last_seen = {n: next((i for i, d in enumerate(reversed(draws)) if n in d.numbers), len(draws)) for n in range(1, 40)}
    odd_even = Counter(sum(n % 2 for n in d.numbers) for d in draws)
    small_large = Counter(sum(n <= 19 for n in d.numbers) for d in draws)
    sums = [sum(d.numbers) for d in draws]
    consecutive = Counter(sum(b == a + 1 for a, b in zip(d.numbers, d.numbers[1:])) for d in draws)
    repeats = Counter(len(set(a.numbers) & set(b.numbers)) for a, b in zip(draws, draws[1:]))
    return {"frequencies": frequencies, "tails": tails, "pairs": pairs, "missing": last_seen,
            "odd_even": odd_even, "small_large": small_large, "sums": sums,
            "consecutive": consecutive, "repeats": repeats}


def windows(draws: list[Draw]) -> dict[str, dict]:
    recent = {str(size): snapshot(draws[-size:]) for size in (10, 30, 100)}
    cutoff = draws[-1].date - timedelta(days=365 * 5 + 2) if draws else None
    recent["5y"] = snapshot([draw for draw in draws if draw.date >= cutoff]) if cutoff else snapshot([])
    return recent


def sum_interval(draws: list[Draw]) -> tuple[int, int]:
    sums = [sum(draw.numbers) for draw in draws]
    if len(sums) < 4:
        return (60, 140)
    q1, _, q3 = quantiles(sums, n=4, method="inclusive")
    return int(q1), int(q3)

