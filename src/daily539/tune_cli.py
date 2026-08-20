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
        "# 今彩539 中 3+ 直接優化驗證",
        "",
        f"- 模型：{result['model']}",
        f"- 搜尋結構數：{result['searched_configs']}",
        f"- 訓練期數：{result['training_periods']}",
        f"- 保留驗證期數：{result['validation_periods']}",
        f"- 升級門檻：至少 {result['promotion_threshold']}/{result['validation_periods']} 次中 3+",
        "",
        "## 訓練區排名",
        "",
    ]

    for rank, item in enumerate(result["training_leaders"], start=1):
        lines.extend([
            f"### 第 {rank} 名",
            "",
            f"- 結構：`{_format_config(item['config'])}`",
            f"- 訓練中 3+：{item['three_plus']}/{result['training_periods']}",
            f"- 訓練中 4+：{item['four_plus']}/{result['training_periods']}",
            f"- 訓練中 2+：{item['two_plus']}/{result['training_periods']}",
            f"- 訓練 ROI：{item['roi']:.1%}",
            "",
        ])

    selected = result["selected"]
    lines.extend(["## 保留驗證結果", ""])
    if selected is None:
        lines.append("- 無可用結果")
    else:
        valid = selected["validation"]
        verdict = "通過，可進入升級候選" if result["promote"] else "未通過，維持目前每日模型"
        lines.extend([
            f"- 事先選定結構：`{_format_config(selected['config'])}`",
            f"- 中 3+：{valid['three_plus']}/{result['validation_periods']} ({valid['three_plus'] / result['validation_periods']:.2%})",
            f"- 中 4+：{valid['four_plus']}/{result['validation_periods']}",
            f"- 中 2+：{valid['two_plus']}/{result['validation_periods']}",
            f"- ROI：{valid['roi']:.1%}",
            f"- 命中分布：{dict(sorted(valid['distribution'].items()))}",
            f"- 判定：**{verdict}**",
            "",
            "> 最終結構只依訓練區排名選定；最近 365 期僅驗證一次。未達升級門檻不改每日模型。",
        ])

    path = Path("reports/tuning.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
