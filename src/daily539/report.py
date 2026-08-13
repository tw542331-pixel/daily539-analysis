from pathlib import Path

from .analysis import windows
from .models import Draw
from .strategy import combo_factors, number_scores


def _two_plus(distribution: dict) -> int:
    return sum(count for hits, count in distribution.items() if hits >= 2)


def _rate(count: int, total: int) -> str:
    return f"{count / total:.1%}" if total else "—"


def render(draws: list[Draw], picks: list[tuple[int, ...]], strategy: dict,
           random_hits: dict, legacy_hits: dict | None = None) -> str:
    analyses = windows(draws)
    latest = draws[-1]
    legacy_hits = legacy_hits or {}
    scores = number_scores(draws)
    lines = [
        "# 今彩539 最新分析", "",
        f"資料截止：{latest.date.isoformat()}（{len(draws)} 期）", "",
        "## 最新開獎結果", "",
        f"- 開獎日期：{latest.date.isoformat()}",
        f"- 期別：{latest.period}",
        "- 開獎號碼：" + " ".join(f"{n:02d}" for n in latest.numbers), "",
        "## 候選組合", "",
    ]
    for index, pick in enumerate(picks, 1):
        factors = combo_factors(draws, pick, scores)
        lines += [
            f"- 第 {index} 組：{' '.join(f'{n:02d}' for n in pick)}",
            (f"  - 相對分數 {factors['total']:.2f}（單號 {factors['number']:.2f}、"
             f"二碼 {factors['pair']:+.2f}、和值 {factors['sum']:+.2f}、"
             f"尾數 {factors['tail']:+.2f}、重號 {factors['repeat']:+.2f}）"),
        ]
    lines += [
        "",
        "> 分數只用於組合排序，不是中獎機率。兩組優先完全不重複，以涵蓋 10 個不同號碼。",
        "",
        "### 模型實際使用的資料", "",
        "- 單號：近 10、30、100 期與近 5 年頻率，先標準化再加權。",
        "- 遺漏：只給小幅且有上限的分數，不把久未開視為『該開了』。",
        "- 組合：近 100 期二碼、和值位置、尾數分散及與前期重號。",
        "- 約束：奇偶與大小各採 2:3 或 3:2，排除過度集中與極端組合。",
    ]
    for label, stats in analyses.items():
        hot = stats["frequencies"].most_common(10)
        cold = sorted(range(1, 40), key=lambda n: (stats["frequencies"][n], n))[:10]
        lines += [
            "", f"## 近 {label} 期統計" if label != "5y" else "## 近 5 年統計", "",
            "- 熱門號：" + "、".join(f"{n:02d}({c})" for n, c in hot),
            "- 冷門號：" + "、".join(f"{n:02d}({stats['frequencies'][n]})" for n in cold),
            "- 遺漏最高：" + "、".join(
                f"{n:02d}({c})" for n, c in sorted(stats["missing"].items(), key=lambda x: -x[1])[:10]),
            "- 尾數：" + "、".join(f"{n}尾({stats['tails'][n]})" for n in range(10)),
            "- 奇數個數分布：" + str(dict(sorted(stats["odd_even"].items()))),
            "- 小號個數分布：" + str(dict(sorted(stats["small_large"].items()))),
            f"- 和值範圍：{min(stats['sums'], default=0)}～{max(stats['sums'], default=0)}",
            "- 連號鄰接數：" + str(dict(sorted(stats["consecutive"].items()))),
            "- 與前期重號數：" + str(dict(sorted(stats["repeats"].items()))),
            "- 常見二碼：" + "、".join(
                f"{a:02d}-{b:02d}({c})" for (a, b), c in stats["pairs"].most_common(10)),
        ]
    tested_periods = sum(strategy.values())
    strategy_two = _two_plus(strategy)
    legacy_two = _two_plus(legacy_hits)
    random_two = _two_plus(random_hits)
    lines += [
        "", f"## 向前回測（最近 {tested_periods} 期）", "",
        "> 每一期只使用該期以前資料；各方法每期都取兩組中的最佳命中數。", "",
        f"- 重作模型：{dict(sorted(strategy.items()))}",
        f"- 舊版模型：{dict(sorted(legacy_hits.items()))}" if legacy_hits else "- 舊版模型：未提供",
        f"- 單次隨機基準：{dict(sorted(random_hits.items()))}", "",
        "### 至少中 2 碼", "",
        f"- 重作模型：{strategy_two}/{tested_periods}（{_rate(strategy_two, tested_periods)}）",
        f"- 舊版模型：{legacy_two}/{tested_periods}（{_rate(legacy_two, tested_periods)}）"
        if legacy_hits else "- 舊版模型：未提供",
        f"- 單次隨機基準：{random_two}/{tested_periods}（{_rate(random_two, tested_periods)}）", "",
    ]
    if legacy_hits:
        lines.append(f"> 本樣本重作模型比舊版多 {strategy_two - legacy_two:+d} 期至少中 2 碼；"
                     "這是歷史樣本結果，不代表下一期有優勢。")
        lines.append("")
    lines += ["> 彩券是隨機事件；不要追損，本報告不保證獲利。", ""]
    return "\n".join(lines)


def save_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
