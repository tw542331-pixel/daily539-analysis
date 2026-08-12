import csv
from pathlib import Path

from .models import Draw


def load_draws(path: Path) -> list[Draw]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [Draw(__import__("datetime").date.fromisoformat(row["date"]), row["period"],
                     tuple(int(n) for n in row["numbers"].split())) for row in csv.DictReader(handle)]


def save_draws(path: Path, draws: list[Draw]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("date", "period", "numbers"))
        for draw in sorted(draws):
            writer.writerow((draw.date.isoformat(), draw.period, " ".join(f"{n:02d}" for n in draw.numbers)))

