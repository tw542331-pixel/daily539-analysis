from datetime import date
from pathlib import Path

from .analysis import windows
from .models import Draw
from .performance import TICKET_PRICE, next_draw_date
from .strategy import combo_factors, number_scores
from .validation import (THREE_PLUS_RANDOM_PROBABILITY, assess_three_hit,
                         three_plus_count)


def _two_plus(distribution: dict) -> int:
    return sum(count for hits, count in distribution.items() if hits >= 2)


def _rate(count: int, total: int) -> str:
    return f"{count / total:.1%}" if total else "—"


def _roi(cost: int, payout: int) -> str:
    return f"{(payout - cost) / cost:.1%}" if cost else "—"


def _backtest_financial_line(label: str, rows: list[dict], prefix: str) -> str:
    cost = len(rows) * TICKET_PRICE * 2
    payout = sum(int(row[f"{prefix}_payout"]) for row in rows)
    return (f"- {label}：投入 {cost:,} 元、獎金 {payout:,} 元、"
            f"淨損益 {payout - cost:+,} 元、ROI {_roi(cost, payout)}")


def render(draws: list[Draw], picks: list[tuple[int, ...]], strategy: dict,
           random_hits: dict, legacy_hits: dict | None = None,
           live_results: list[dict] | None = None,
           backtest_rows: list[dict] | None = None,
           target_date: date | None = None) -> str:
    analyses = windows(draws)
    latest = draws[-1]
    legacy_hits = legacy_hits or {}
    live_results = live_results or []
    backtest_rows = backtest_rows or []
    target_date = target_date or next_draw_date(latest.date)
    scores = number_scores(draws)
    three_hit = assess_three_hit(strategy)
    if not three_hit.periods:
        gate_status = "資料不足；以下僅為研究候選，不建議下注"
    elif three_hit.passed:
        gate_status = "通過最低統計門檻；仍不代表下一期有優勢"
    else:
        gate_status = "未通過；以下僅為研究候選，不建議下注"
    candidate_heading = ("### 候選組合（通過中 3 碼門檻）" if three_hit.passed
                         else "### 研究候選組合（未達投注門檻）")
    lines = [
        "# 今彩539 最新分析", "",
        f"資料截止：{latest.date.isoformat()}（{len(draws)} 期）", "",
        "## 中 3 碼目標判定", "",
        "- 核心目標：每期兩組中，至少一組命中 3 碼以上。",
        (f"- 最近 {three_hit.periods} 期模型：{three_hit.successes}/{three_hit.periods}"
         f"（{_rate(three_hit.successes, three_hit.periods)}）"),
        (f"- 兩組不重複隨機理論：{THREE_PLUS_RANDOM_PROBABILITY:.2%}"
         f"（同樣期數預期 {three_hit.expected:.1f} 次）"),
        (f"- 模型升級門檻：至少 {three_hit.threshold}/{three_hit.periods}"
         "（單尾 5% 顯著水準）" if three_hit.periods else "- 模型升級門檻：等待足夠回測資料"),
        f"- 判定：{gate_status}", "",
        "> 門檻只代表最低統計證據，不是中獎保證；驗證方法與失敗實驗見 `reports/three-hit-validation.md`。", "",
        "## 下一期預測", "",
        f"- 目標開獎日：{target_date.isoformat()}",
        f"- 預測依據：截至 {latest.date.isoformat()} 第 {latest.period} 期", "",
        candidate_heading, "",
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
        "> 相對分數只用於組合排序，不是中獎率。兩組優先完全不重複，以涵蓋 10 個不同號碼。",
        "",
        "## 最新開獎結果", "",
        f"- 開獎日期：{latest.date.isoformat()}",
        f"- 期別：{latest.period}",
        "- 開獎號碼：" + " ".join(f"{n:02d}" for n in latest.numbers),
    ]

    if live_results:
        last = live_results[-1]
        lines += ["", "### 上一期預測對獎", ""]
        for index, (pick, hits) in enumerate(zip(last["picks"], last["ticket_hits"]), 1):
            matched = sorted(set(pick) & set(last["actual"]))
            matched_text = " ".join(f"{number:02d}" for number in matched) or "無"
            lines.append(f"- 第 {index} 組：命中 {hits} 碼（{matched_text}）")
        lines += [
            f"- 當期投入：{last['cost']:,} 元",
            f"- 當期獎金：{last['payout']:,} 元",
            f"- 當期損益：{last['net']:+,} 元",
        ]

        live_cost = sum(row["cost"] for row in live_results)
        live_payout = sum(row["payout"] for row in live_results)
        prize_periods = sum(max(row["ticket_hits"]) >= 2 for row in live_results)
        profit_periods = sum(row["net"] > 0 for row in live_results)
        lines += [
            "", "## 實戰累積績效", "",
            f"- 已結算：{len(live_results)} 期",
            f"- 累積投入：{live_cost:,} 元",
            f"- 累積獎金：{live_payout:,} 元",
            f"- 累積淨損益：{live_payout - live_cost:+,} 元",
            f"- 實戰 ROI：{_roi(live_cost, live_payout)}",
            f"- 達獎期數：{prize_periods}/{len(live_results)}；實際獲利期數："
            f"{profit_periods}/{len(live_results)}",
            "",
            "> 中 2 碼不等於獲利；每期買兩組投入 100 元，單組中 2 碼只拿回 50 元。",
        ]

    lines += [
        "",
        "## 模型實際使用的資料", "",
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
    strategy_three = three_plus_count(strategy)
    legacy_three = three_plus_count(legacy_hits)
    random_three = three_plus_count(random_hits)
    lines += [
        "", f"## 向前回測（最近 {tested_periods} 期）", "",
        "> 每一期只使用該期以前資料；各方法每期都取兩組中的最佳命中數。", "",
        f"- 重作模型：{dict(sorted(strategy.items()))}",
        f"- 舊版模型：{dict(sorted(legacy_hits.items()))}" if legacy_hits else "- 舊版模型：未提供",
        f"- 兩組不重複隨機基準：{dict(sorted(random_hits.items()))}", "",
        "### 至少中 3 碼（單期必定獲利）", "",
        f"- 重作模型：{strategy_three}/{tested_periods}（{_rate(strategy_three, tested_periods)}）",
        f"- 舊版模型：{legacy_three}/{tested_periods}（{_rate(legacy_three, tested_periods)}）"
        if legacy_hits else "- 舊版模型：未提供",
        f"- 兩組不重複隨機基準：{random_three}/{tested_periods}（{_rate(random_three, tested_periods)}）", "",
        "### 至少中 2 碼（僅達最低獎項）", "",
        f"- 重作模型：{strategy_two}/{tested_periods}（{_rate(strategy_two, tested_periods)}）",
        f"- 舊版模型：{legacy_two}/{tested_periods}（{_rate(legacy_two, tested_periods)}）"
        if legacy_hits else "- 舊版模型：未提供",
        f"- 兩組不重複隨機基準：{random_two}/{tested_periods}（{_rate(random_two, tested_periods)}）", "",
    ]
    if backtest_rows:
        lines += [
            "### 回測損益（每期兩組、每注 50 元）", "",
            _backtest_financial_line("重作模型", backtest_rows, "strategy"),
            _backtest_financial_line("舊版模型", backtest_rows, "legacy"),
            _backtest_financial_line("兩組不重複隨機基準", backtest_rows, "random"),
            "",
            "> 回測 ROI 才反映投注成本與獎金；『至少中 2 碼』只代表達到最低獎項。",
            "",
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
