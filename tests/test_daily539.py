from datetime import date, timedelta

import pytest

from daily539.analysis import snapshot
from daily539.backtest import run
from daily539.models import Draw
from daily539.performance import (Prediction, load_predictions, next_draw_date,
                                  payout_for_hits, record_prediction, save_predictions,
                                  settle_predictions)
from daily539.report import render
from daily539.source import _parse_record, _records
from daily539.strategy import combo_factors, select, valid_combo


def draws(count=130):
    return [Draw(date(2025, 1, 1) + timedelta(days=i), str(i),
                 tuple(sorted({(i * 7 + j * 8) % 39 + 1 for j in range(5)}))) for i in range(count)]


def test_official_record_parser_supports_roc_date():
    draw = _parse_record({"drawTerm": "113000001", "drawDate": "113/01/02", "drawNumberSize": [5, 1, 39, 20, 9]})
    assert draw.date == date(2024, 1, 2)
    assert draw.numbers == (1, 5, 9, 20, 39)


def test_official_response_parser_supports_daily539res_envelope():
    record = {
        "drawTerm": "115000195",
        "drawDate": "115/08/13",
        "drawNumberSize": [7, 12, 17, 20, 32],
    }
    payload = {
        "content": {
            "daily539Res": [record],
            "totalSize": 1,
        },
        "success": True,
    }

    assert list(_records(payload)) == [record]
    draw = _parse_record(list(_records(payload))[0])
    assert draw.period == "115000195"
    assert draw.date == date(2026, 8, 13)
    assert draw.numbers == (7, 12, 17, 20, 32)


def test_report_displays_latest_draw_result():
    latest = Draw(date(2026, 8, 13), "115000195", (7, 12, 17, 20, 32))
    report = render([latest], [(6, 8, 21, 25, 36)], {}, {})

    assert "## 最新開獎結果" in report
    assert "- 開獎日期：2026-08-13" in report
    assert "- 期別：115000195" in report
    assert "- 開獎號碼：07 12 17 20 32" in report
    assert "- 目標開獎日：2026-08-14" in report


def test_next_draw_date_skips_sunday():
    assert next_draw_date(date(2026, 8, 15)) == date(2026, 8, 17)
    assert next_draw_date(date(2026, 8, 17)) == date(2026, 8, 18)


def test_prediction_history_is_preserved_and_settled(tmp_path):
    path = tmp_path / "predictions.csv"
    source = Draw(date(2026, 8, 17), "115000199", (19, 22, 27, 28, 38))
    picks = [(7, 8, 12, 21, 35), (6, 16, 19, 25, 37)]
    predictions, current = record_prediction([], source, picks)
    save_predictions(path, predictions)

    loaded = load_predictions(path)
    assert loaded == predictions
    assert current.target_date == date(2026, 8, 18)

    actual = Draw(date(2026, 8, 18), "115000200", (5, 6, 10, 28, 39))
    settled = settle_predictions(loaded, [source, actual])
    assert settled[0]["ticket_hits"] == [0, 1]
    assert settled[0]["cost"] == 100
    assert settled[0]["payout"] == 0
    assert settled[0]["net"] == -100


def test_prize_calculation_counts_each_ticket():
    assert payout_for_hits([2, 1]) == 50
    assert payout_for_hits([2, 2]) == 100
    assert payout_for_hits([3, 0]) == 300


def test_report_displays_live_profit_and_loss():
    latest = Draw(date(2026, 8, 18), "115000200", (5, 6, 10, 28, 39))
    prediction = Prediction(date(2026, 8, 18), "115000199",
                            ((7, 8, 12, 21, 35), (6, 16, 19, 25, 37)))
    live_results = settle_predictions([prediction], [latest])
    report = render([latest], [(7, 12, 19, 28, 35), (6, 8, 11, 21, 25)],
                    {}, {}, live_results=live_results)

    assert "## 實戰累積績效" in report
    assert "- 累積投入：100 元" in report
    assert "- 累積獎金：0 元" in report
    assert "- 累積淨損益：-100 元" in report
    assert "- 實戰 ROI：-100.0%" in report


def test_statistics_and_constraints():
    history = draws()
    assert sum(snapshot(history[-10:])["frequencies"].values()) == 50
    picks = select(history, seed=1)
    assert len(picks) == 2 and all(valid_combo(p, (60, 140)) for p in picks)
    assert not (set(picks[0]) & set(picks[1]))


def test_rebuilt_strategy_is_deterministic_and_explainable():
    history = draws()
    first = select(history, seed=1)
    assert first == select(history, seed=999)
    factors = combo_factors(history, first[0])
    assert set(factors) == {"number", "pair", "sum", "tail", "repeat", "total"}
    assert factors["total"] == pytest.approx(sum(value for key, value in factors.items() if key != "total"))


def test_backtest_never_passes_current_draw(monkeypatch):
    history = draws(30)
    lengths = []
    monkeypatch.setattr("daily539.backtest.select", lambda prior, seed: lengths.append(len(prior)) or [(1, 2, 20, 21, 39)] * 2)
    monkeypatch.setattr("daily539.backtest.select_legacy", lambda prior, seed: [(1, 2, 20, 21, 39)] * 2)
    _, _, _, rows = run(history, warmup=10)
    assert lengths == list(range(10, 30))
    assert len(rows) == 20


def test_backtest_can_limit_recent_periods(monkeypatch):
    history = draws(30)
    lengths = []
    monkeypatch.setattr("daily539.backtest.select", lambda prior, seed: lengths.append(len(prior)) or [(1, 2, 20, 21, 39)] * 2)
    monkeypatch.setattr("daily539.backtest.select_legacy", lambda prior, seed: [(1, 2, 20, 21, 39)] * 2)
    _, _, _, rows = run(history, warmup=10, periods=5)
    assert lengths == list(range(25, 30))
    assert len(rows) == 5
    for row in rows:
        first, second = row["random_picks"].split("|")
        assert not (set(first.split()) & set(second.split()))
        assert "strategy_payout" in row


def test_backtest_rejects_non_positive_periods():
    with pytest.raises(ValueError, match="positive"):
        run(draws(30), periods=0)
