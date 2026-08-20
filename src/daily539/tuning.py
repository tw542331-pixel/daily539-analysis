from __future__ import annotations

from .backtest import evaluate_three_hit_config, rank_three_hit_configs
from .models import Draw
from .three_hit import ThreeHitConfig
from .validation import promotion_threshold


TRAINING_PERIODS = 730
VALIDATION_PERIODS = 365


def candidate_configs() -> list[ThreeHitConfig]:
    """Small structural search focused directly on 3+ hits."""
    return [
        ThreeHitConfig(window=30, pool_size=12, triple_weight=1.00, number_weight=0.20, max_overlap=0),
        ThreeHitConfig(window=30, pool_size=14, triple_weight=1.00, number_weight=0.35, max_overlap=0),
        ThreeHitConfig(window=60, pool_size=12, triple_weight=1.00, number_weight=0.20, max_overlap=0),
        ThreeHitConfig(window=60, pool_size=14, triple_weight=1.00, number_weight=0.35, max_overlap=0),
        ThreeHitConfig(window=100, pool_size=14, triple_weight=1.00, number_weight=0.20, max_overlap=0),
        ThreeHitConfig(window=100, pool_size=16, triple_weight=1.00, number_weight=0.35, max_overlap=0),
        ThreeHitConfig(window=200, pool_size=14, triple_weight=1.00, number_weight=0.20, max_overlap=0),
        ThreeHitConfig(window=200, pool_size=16, triple_weight=1.00, number_weight=0.35, max_overlap=0),
    ]


def tune_and_validate(
    draws: list[Draw],
    seed: int = 539,
    top_n: int = 5,
) -> dict:
    """Select one 3+-optimized structure on training data, then validate it once."""
    minimum = 100 + TRAINING_PERIODS + VALIDATION_PERIODS
    if len(draws) < minimum:
        raise ValueError(
            f"need at least {minimum} draws for tuning + holdout validation; got {len(draws)}"
        )
    if top_n < 1:
        raise ValueError("top_n must be positive")

    validation_start = len(draws) - VALIDATION_PERIODS
    training_draws = draws[:validation_start]
    configs = candidate_configs()
    training_results = rank_three_hit_configs(
        training_draws,
        configs,
        periods=TRAINING_PERIODS,
        seed=seed,
    )

    training_leaders = training_results[:top_n]
    if not training_leaders:
        return {
            "model": "three_hit_optimizer",
            "searched_configs": len(configs),
            "training_periods": TRAINING_PERIODS,
            "validation_periods": VALIDATION_PERIODS,
            "promotion_threshold": promotion_threshold(VALIDATION_PERIODS),
            "top_n": top_n,
            "training_leaders": [],
            "selected": None,
            "promote": False,
        }

    selected_training = training_leaders[0]
    selected_config = selected_training["config"]
    validation_result = evaluate_three_hit_config(
        draws,
        selected_config,
        periods=VALIDATION_PERIODS,
        seed=seed,
    )
    threshold = promotion_threshold(VALIDATION_PERIODS)
    promote = validation_result["three_plus"] >= threshold

    return {
        "model": "three_hit_optimizer",
        "searched_configs": len(configs),
        "training_periods": TRAINING_PERIODS,
        "validation_periods": VALIDATION_PERIODS,
        "promotion_threshold": threshold,
        "top_n": top_n,
        "training_leaders": training_leaders,
        "selected": {
            "config": selected_config,
            "training": selected_training,
            "validation": validation_result,
        },
        "promote": promote,
    }
