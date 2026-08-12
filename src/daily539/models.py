from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, order=True)
class Draw:
    date: date
    period: str
    numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.numbers) != 5 or len(set(self.numbers)) != 5:
            raise ValueError("a draw must contain five distinct numbers")
        if any(not 1 <= number <= 39 for number in self.numbers):
            raise ValueError("numbers must be between 1 and 39")

