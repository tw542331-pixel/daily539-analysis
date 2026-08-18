from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from .models import Draw


TICKET_PRICE = 50
PRIZES = {0: 0, 1: 0, 2: 50, 3: 300, 4: 20_000, 5: 8_000_000}


@dataclass(frozen=True)
class Prediction:
    target_date: date
    source_period: str
    picks: tuple[tuple[int, ...], ...]


def next_draw_date(latest: date) -> date:
    """Return the next Monday-to-Saturday draw date."""
    target = latest + timedelta(days=1)
    while target.weekday() == 6:
        target += timedelta(days=1)
    return target


def format_picks(picks: tuple[tuple[int, ...], ...] | list[tuple[int, ...]]) -> str:
    return "|".join(" ".join(f"{number:02d}" for number in pick) for pick in picks)


def parse_picks(value: str) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(number) for number in pick.split()) for pick in value.split("|"))


def load_predictions(path: Path) -> list[Prediction]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            Prediction(date.fromisoformat(row["target_date"]), row["source_period"],
                       parse_picks(row["picks"]))
            for row in csv.DictReader(handle)
        ]


def save_predictions(path: Path, predictions: list[Prediction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("target_date", "source_period", "picks"),
                                lineterminator="\n")
        writer.writeheader()
        for prediction in sorted(predictions, key=lambda item: item.target_date):
            writer.writerow({"target_date": prediction.target_date.isoformat(),
                             "source_period": prediction.source_period,
                             "picks": format_picks(prediction.picks)})


def record_prediction(predictions: list[Prediction], source: Draw,
                      picks: list[tuple[int, ...]]) -> tuple[list[Prediction], Prediction]:
    target = next_draw_date(source.date)
    existing = next((item for item in predictions if item.target_date == target), None)
    if existing:
        return predictions, existing
    prediction = Prediction(target, source.period, tuple(picks))
    return predictions + [prediction], prediction


def payout_for_hits(hits: list[int] | tuple[int, ...]) -> int:
    return sum(PRIZES[hit] for hit in hits)


def settle_predictions(predictions: list[Prediction], draws: list[Draw]) -> list[dict]:
    by_date = {draw.date: draw for draw in draws}
    settled = []
    for prediction in sorted(predictions, key=lambda item: item.target_date):
        actual = by_date.get(prediction.target_date)
        if not actual:
            continue
        actual_numbers = set(actual.numbers)
        ticket_hits = [len(set(pick) & actual_numbers) for pick in prediction.picks]
        payout = payout_for_hits(ticket_hits)
        cost = TICKET_PRICE * len(prediction.picks)
        settled.append({
            "target_date": prediction.target_date,
            "period": actual.period,
            "actual": actual.numbers,
            "picks": prediction.picks,
            "ticket_hits": ticket_hits,
            "cost": cost,
            "payout": payout,
            "net": payout - cost,
        })
    return settled
