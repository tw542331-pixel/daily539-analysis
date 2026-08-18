from dataclasses import dataclass
from math import comb


TOTAL_NUMBERS = 39
DRAW_SIZE = 5
TICKETS_PER_PERIOD = 2


def disjoint_two_ticket_three_plus_probability() -> float:
    """Exact P(at least one disjoint five-number ticket hits 3+)."""
    total_draws = comb(TOTAL_NUMBERS, DRAW_SIZE)
    single_ticket = sum(
        comb(DRAW_SIZE, hits) * comb(TOTAL_NUMBERS - DRAW_SIZE, DRAW_SIZE - hits)
        for hits in range(3, DRAW_SIZE + 1)
    ) / total_draws
    # Two disjoint tickets cannot both hit 3+ in the same five-number draw.
    return TICKETS_PER_PERIOD * single_ticket


THREE_PLUS_RANDOM_PROBABILITY = disjoint_two_ticket_three_plus_probability()


def three_plus_count(distribution: dict[int, int]) -> int:
    return sum(count for hits, count in distribution.items() if hits >= 3)


def _binomial_tail(periods: int, successes: int, probability: float) -> float:
    return sum(
        comb(periods, hits)
        * probability ** hits
        * (1 - probability) ** (periods - hits)
        for hits in range(successes, periods + 1)
    )


def promotion_threshold(periods: int, alpha: float = 0.05) -> int:
    """Smallest hit count that beats random at one-sided significance alpha."""
    if periods <= 0:
        return 0
    for successes in range(periods + 1):
        if _binomial_tail(periods, successes, THREE_PLUS_RANDOM_PROBABILITY) <= alpha:
            return successes
    return periods


@dataclass(frozen=True)
class ThreeHitAssessment:
    periods: int
    successes: int
    expected: float
    threshold: int
    passed: bool

    @property
    def rate(self) -> float:
        return self.successes / self.periods if self.periods else 0.0


def assess_three_hit(distribution: dict[int, int], alpha: float = 0.05) -> ThreeHitAssessment:
    periods = sum(distribution.values())
    successes = three_plus_count(distribution)
    threshold = promotion_threshold(periods, alpha)
    return ThreeHitAssessment(
        periods=periods,
        successes=successes,
        expected=periods * THREE_PLUS_RANDOM_PROBABILITY,
        threshold=threshold,
        passed=bool(periods) and successes >= threshold,
    )
