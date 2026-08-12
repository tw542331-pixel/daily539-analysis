from pathlib import Path

from .analysis import windows
from .models import Draw


def render(draws: list[Draw], picks: list[tuple[int, ...]], strategy: dict, random_hits: dict) -> str:
    analyses = windows(draws)
    lines = ["# 今彩539 最新分析", "", f"資料截止：{draws[-1].date.isoformat()}（{len(draws)} 期）", "",
             "## 建議組合", ""]
    lines += [f"- {' '.join(f'{n:02d}' for n in pick)}" for pick in picks]
    for label, stats in analyses.items():
        hot = stats["frequencies"].most_common(10)
        cold = sorted(range(1, 40), key=lambda n: (stats["frequencies"][n], n))[:10]
        lines += ["", f"## 近 {label} 期統計" if label != "5y" else "## 近 5 年統計",
                  "", "- 熱門號：" + "、".join(f"{n:02d}({c})" for n, c in hot),
                  "- 冷門號：" + "、".join(f"{n:02d}({stats['frequencies'][n]})" for n in cold),
                  "- 遺漏最高：" + "、".join(f"{n:02d}({c})" for n, c in sorted(stats["missing"].items(), key=lambda x: -x[1])[:10]),
                  "- 尾數：" + "、".join(f"{n}尾({stats['tails'][n]})" for n in range(10)),
                  "- 奇數個數分布：" + str(dict(sorted(stats["odd_even"].items()))),
                  "- 小號個數分布：" + str(dict(sorted(stats["small_large"].items()))),
                  f"- 和值範圍：{min(stats['sums'], default=0)}～{max(stats['sums'], default=0)}",
                  "- 連號鄰接數：" + str(dict(sorted(stats["consecutive"].items()))),
                  "- 與前期重號數：" + str(dict(sorted(stats["repeats"].items()))),
                  "- 常見二碼：" + "、".join(f"{a:02d}-{b:02d}({c})" for (a, b), c in stats["pairs"].most_common(10))]
    lines += ["", "## 滾動回測", "", "> 每一期只使用該期以前資料；隨機基準同樣每期兩組。",
              "", f"- 分析策略命中分布：{dict(sorted(strategy.items()))}",
              f"- 隨機選號命中分布：{dict(sorted(random_hits.items()))}", "",
              "> 彩券結果為隨機事件，本報告僅供統計研究，不保證獲利。", ""]
    return "\n".join(lines)


def save_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

