from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path

from .models import Draw
from .performance import format_picks, payout_for_hits
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
        random_numbers = rng.sample(range(1, 40), 10)
        baselines = [tuple(sorted(random_numbers[:5])), tuple(sorted(random_numbers[5:]))]
        strategy_ticket_hits = [len(set(pick) & actual) for pick in picks]
        legacy_ticket_hits = [len(set(pick) & actual) for pick in legacy_picks]
        random_ticket_hits = [len(set(pick) & actual) for pick in baselines]
        sh = max(strategy_ticket_hits)
        lh = max(legacy_ticket_hits)
        rh = max(random_ticket_hits)
        strategy[sh] += 1; legacy[lh] += 1; random_hits[rh] += 1
        rows.append({"date": draws[index].date.isoformat(), "period": draws[index].period,
                     "strategy_hits": sh, "legacy_hits": lh, "random_hits": rh,
                     "strategy_ticket_hits": "|".join(map(str, strategy_ticket_hits)),
                     "legacy_ticket_hits": "|".join(map(str, legacy_ticket_hits)),
                     "random_ticket_hits": "|".join(map(str, random_ticket_hits)),
                     "strategy_payout": payout_for_hits(strategy_ticket_hits),
                     "legacy_payout": payout_for_hits(legacy_ticket_hits),
                     "random_payout": payout_for_hits(random_ticket_hits),
                     "picks": format_picks(picks),
                     "legacy_picks": format_picks(legacy_picks),
                     "random_picks": format_picks(baselines)})
    return strategy, legacy, random_hits, rows


def save_results(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("date", "period", "strategy_hits", "legacy_hits",
                        "random_hits", "strategy_ticket_hits", "legacy_ticket_hits",
                        "random_ticket_hits", "strategy_payout", "legacy_payout",
                        "random_payout", "picks", "legacy_picks", "random_picks"),
            lineterminator="\n",
        )
        writer.writeheader(); writer.writerows(rows)
