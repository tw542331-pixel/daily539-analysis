from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .storage import load_draws
from .tuning import tune_and_validate


def _format_config(config) -> str:
    values = asdict(config)
    return ", ".join(f"{key}={value}" for key, value in values.items())


def main() -> None:
    draws = load_draws(Path("data/draws.csv"))
    result = tune_and_validate(draws)

    lines = [
        "# 今彩539 模型調參驗證",
        "",
        f"- 搜尋參數組數：{result['searched_configs']}",
        f"- 訓練期數：{result['training_periods']}",
        f"- 驗證期數：{result['validation_periods']}",
        f"- 進入驗證的候選數：{result['top_n']}",
        "",
        "## 驗證結果排名",
        "",
    ]

    for rank, item in enumerate(result["results"], start=1):
        train = item["training"]
        valid = item["validation"]
        lines.extend([
            f"### 第 {rank} 名",
            "",
            f"- 參數：`{_format_config(item['config'])}`",
            f"- 訓練中 3+：{train['three_plus']}/{result['training_periods']}",
            f"- 驗證中 3+：{valid['three_plus']}/{result['validation_periods']}",
            f"- 驗證中 4+：{valid['four_plus']}/{result['validation_periods']}",
            f"- 驗證中 2+：{valid['two_plus']}/{result['validation_periods']}",
            f"- 驗證 ROI：{valid['roi']:.1%}",
            f"- 驗證分布：{dict(sorted(valid['distribution'].items()))}",
            "",
        ])

    best = result["best"]
    lines.extend([
        "## 最佳驗證結果",
        "",
    ])
    if best is None:
        lines.append("- 無可用結果")
    else:
        valid = best["validation"]
        lines.extend([
            f"- 最佳參數：`{_format_config(best['config'])}`",
            f"- 中 3+：{valid['three_plus']}/{result['validation_periods']} ({valid['three_plus'] / result['validation_periods']:.2%})",
            f"- 中 4+：{valid['four_plus']}/{result['validation_periods']}",
            f"- ROI：{valid['roi']:.1%}",
            "",
            "> 此結果使用最近 365 期作保留驗證；驗證資料未參與參數搜尋。",
        ])

    path = Path("reports/tuning.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
