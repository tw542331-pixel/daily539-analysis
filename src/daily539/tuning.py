from __future__ import annotations

from .backtest import evaluate_config, rank_configs
from .models import Draw
from .strategy import StrategyConfig


TRAINING_PERIODS = 730
VALIDATION_PERIODS = 365


def candidate_configs() -> list[StrategyConfig]:
    """Return a small, auditable candidate set to reduce runtime and overfitting."""
    return [
        StrategyConfig(),
        StrategyConfig(weight_10=0.20, weight_30=0.35, weight_100=0.65, weight_5y=0.25),
        StrategyConfig(weight_10=0.20, weight_30=0.50, weight_100=0.65, weight_5y=0.10),
        StrategyConfig(weight_10=0.35, weight_30=0.50, weight_100=0.50, weight_5y=0.10),
        StrategyConfig(weight_10=0.50, weight_30=0.35, weight_100=0.35, weight_5y=0.10),
        StrategyConfig(weight_10=0.20, weight_30=0.35, weight_100=0.50, weight_5y=0.40),
        StrategyConfig(missing_weight=0.00),
        StrategyConfig(missing_weight=0.30),
        StrategyConfig(pair_weight=0.00),
        StrategyConfig(pair_weight=0.30),
        StrategyConfig(sum_weight=0.00, tail_weight=0.00, repeat_weight=0.00),
        StrategyConfig(pair_weight=0.30, sum_weight=0.00, tail_weight=0.00, repeat_weight=0.00),
    ]


def tune_and_validate(
    draws: list[Draw],
    seed: int = 539,
    top_n: int = 5,
) -> dict:
    """Tune on older draws, select once, then evaluate once on untouched recent draws."""
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
    training_results = rank_configs(
        training_draws,
        configs,
        periods=TRAINING_PERIODS,
        seed=seed,
    )

    training_leaders = training_results[:top_n]
    if not training_leaders:
        return {
            "searched_configs": len(configs),
            "training_periods": TRAINING_PERIODS,
            "validation_periods": VALIDATION_PERIODS,
            "top_n": top_n,
            "training_leaders": [],
            "selected": None,
        }

    selected_training = training_leaders[0]
    selected_config = selected_training["config"]
    validation_result = evaluate_config(
        draws,
        selected_config,
        periods=VALIDATION_PERIODS,
        seed=seed,
    )

    return {
        "searched_configs": len(configs),
        "training_periods": TRAINING_PERIODS,
        "validation_periods": VALIDATION_PERIODS,
        "top_n": top_n,
        "training_leaders": training_leaders,
        "selected": {
            "config": selected_config,
            "training": selected_training,
            "validation": validation_result,
        },
    }
