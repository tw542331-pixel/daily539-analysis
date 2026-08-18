import argparse
from datetime import date, timedelta
from pathlib import Path

from .backtest import run, save_results
from .performance import (load_predictions, record_prediction, save_predictions,
                          settle_predictions)
from .report import render, save_report
from .source import TaiwanLotterySource
from .storage import load_draws, save_draws
from .strategy import select


def main() -> None:
    parser = argparse.ArgumentParser(description="台灣今彩539分析")
    parser.add_argument("--no-fetch", action="store_true", help="只使用本機資料")
    parser.add_argument("--source-url", help="替換官方相容端點")
    parser.add_argument("--seed", type=int, default=539, help="舊版與隨機回測基準種子")
    parser.add_argument("--backtest-periods", type=int, default=365, help="滾動回測最近期數")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    data_path = root / "data" / "draws.csv"
    draws = load_draws(data_path)
    if not args.no_fetch:
        end = date.today()
        start = (draws[-1].date + timedelta(days=1)) if draws else end - timedelta(days=365 * 5 + 3)
        if start <= end:
            source = TaiwanLotterySource(args.source_url or TaiwanLotterySource.DEFAULT_URL)
            merged = {draw.period: draw for draw in draws + source.fetch(start, end)}
            draws = sorted(merged.values())
            save_draws(data_path, draws)
    if len(draws) < 10:
        raise SystemExit("資料不足；請先連線官方端點取得資料")
    picks = select(draws, seed=args.seed)
    prediction_path = root / "data" / "predictions.csv"
    predictions, current_prediction = record_prediction(
        load_predictions(prediction_path), draws[-1], picks,
    )
    save_predictions(prediction_path, predictions)
    picks = list(current_prediction.picks)
    live_results = settle_predictions(predictions, draws)
    strategy, legacy_hits, random_hits, rows = run(
        draws, warmup=min(100, max(10, len(draws) // 2)),
        seed=args.seed, periods=args.backtest_periods,
    )
    save_results(root / "data" / "results.csv", rows)
    save_report(
        root / "reports" / "latest.md",
        render(draws, picks, strategy, random_hits, legacy_hits,
               live_results=live_results, backtest_rows=rows,
               target_date=current_prediction.target_date),
    )
    print("建議：", *(" ".join(f"{n:02d}" for n in pick) for pick in picks), sep="\n")


if __name__ == "__main__":
    main()
