from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path

from .models import Draw
from .strategy import select, select_legacy


def run(draws: list[Draw], warmup: int = 100, seed: int = 539,
        periods: int = 365) -> tuple[Counter, Counter, Counter, list[dict]]:
    if periods < 1:
        raise ValueError("backtest periods must be positive")
    strategy, legacy, random_hits, rows = Counter(), Counter(), Counter(), []
    rng = random.Random(seed)
    start = max(warmup, len(draws) - periods)
    for index in range(start, len(draws)):
        history, actual = draws[:index], set(draws[index].numbers)  # strictly earlier draws only
        picks = select(history, seed=seed + index)
        legacy_picks = select_legacy(history, seed=seed + index)
        baselines = [tuple(sorted(rng.sample(range(1, 40), 5))) for _ in range(2)]
        sh = max(len(set(pick) & actual) for pick in picks)
        lh = max(len(set(pick) & actual) for pick in legacy_picks)
        rh = max(len(set(pick) & actual) for pick in baselines)
        strategy[sh] += 1; legacy[lh] += 1; random_hits[rh] += 1
        rows.append({"date": draws[index].date.isoformat(), "period": draws[index].period,
                     "strategy_hits": sh, "legacy_hits": lh, "random_hits": rh,
                     "picks": "|".join(" ".join(f"{n:02d}" for n in pick) for pick in picks),
                     "legacy_picks": "|".join(" ".join(f"{n:02d}" for n in pick) for pick in legacy_picks)})
    return strategy, legacy, random_hits, rows


def save_results(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("date", "period", "strategy_hits", "legacy_hits",
                        "random_hits", "picks", "legacy_picks"),
            lineterminator="\n",
        )
        writer.writeheader(); writer.writerows(rows)
