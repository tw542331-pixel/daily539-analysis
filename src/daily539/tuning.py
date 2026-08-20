from __future__ import annotations

from itertools import product

from .backtest import evaluate_config, rank_configs
from .models import Draw
from .strategy import StrategyConfig


TRAINING_PERIODS = 730
VALIDATION_PERIODS = 365


def candidate_configs() -> list[StrategyConfig]:
    """Generate a deliberately small search grid to limit overfitting and runtime."""
    frequency_weights = (0.20, 0.35, 0.50, 0.65)
    long_weights = (0.10, 0.25, 0.40)
    small_weights = (0.00, 0.10, 0.20)

    configs: list[StrategyConfig] = []
    for w10, w30, w100, w5y, missing, pair, sum_w, tail, repeat in product(
        frequency_weights,
        frequency_weights,
        frequency_weights,
        long_weights,
        small_weights,
        small_weights,
        small_weights,
        small_weights,
        small_weights,
    ):
        configs.append(
            StrategyConfig(
                weight_10=w10,
                weight_30=w30,
                weight_100=w100,
                weight_5y=w5y,
                missing_weight=missing,
                pair_weight=pair,
                sum_weight=sum_w,
                tail_weight=tail,
                repeat_weight=repeat,
            )
        )
    return configs


def tune_and_validate(
    draws: list[Draw],
    seed: int = 539,
    top_n: int = 10,
) -> dict:
    """Tune only on older draws, then evaluate untouched recent 365 draws."""
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
