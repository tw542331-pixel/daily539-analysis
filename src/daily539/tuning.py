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
    """Tune on older draws, then evaluate finalists on untouched recent 365 draws."""
    minimum = 100 + TRAINING_PERIODS + VALIDATION_PERIODS
    if len(draws) < minimum:
        raise ValueError(
            f"need at least {minimum} draws for tuning + holdout validation; got {len(draws)}"
        )

    validation_start = len(draws) - VALIDATION_PERIODS
    training_draws = draws[:validation_start]

    configs = candidate_configs()
    training_results = rank_configs(
        training_draws,
        configs,
        periods=TRAINING_PERIODS,
        seed=seed,
    )

    finalists = training_results[:top_n]
    validation_results = []

    for training_result in finalists:
        config = training_result["config"]
        validation_result = evaluate_config(
            draws,
            config,
            periods=VALIDATION_PERIODS,
            seed=seed,
        )
        validation_results.append({
            "config": config,
            "training": training_result,
            "validation": validation_result,
        })

    validation_results.sort(
        key=lambda result: (
            result["validation"]["three_plus"],
            result["validation"]["four_plus"],
            result["validation"]["roi"],
            result["validation"]["two_plus"],
        ),
        reverse=True,
    )

    return {
        "searched_configs": len(configs),
        "training_periods": TRAINING_PERIODS,
        "validation_periods": VALIDATION_PERIODS,
        "top_n": top_n,
        "results": validation_results,
        "best": validation_results[0] if validation_results else None,
    }
