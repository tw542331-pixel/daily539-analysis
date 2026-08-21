from datetime import date

from daily539.models import Draw
from daily539.three_hit import ThreeHitConfig, select_three_hit


def test_three_hit_selector_expands_pool_when_small_pool_is_infeasible(monkeypatch):
    history = [Draw(date(2026, 1, 1), "1", (1, 2, 3, 4, 5))]
    scores = {number: float(40 - number) for number in range(1, 40)}

    monkeypatch.setattr("daily539.three_hit.number_scores", lambda *args, **kwargs: scores)
    monkeypatch.setattr("daily539.three_hit._triple_scores", lambda *args, **kwargs: {})
    monkeypatch.setattr("daily539.three_hit._combo_score", lambda combo, *args, **kwargs: -sum(combo))

    allowed = {
        (1, 2, 3, 4, 11),
        (5, 6, 7, 8, 12),
    }
    monkeypatch.setattr("daily539.three_hit.valid_combo", lambda combo, interval: combo in allowed)

    picks = select_three_hit(
        history,
        config=ThreeHitConfig(pool_size=10, max_overlap=0),
    )

    assert picks == [(1, 2, 3, 4, 11), (5, 6, 7, 8, 12)]
    assert not (set(picks[0]) & set(picks[1]))
