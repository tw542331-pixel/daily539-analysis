from datetime import date, timedelta

from daily539.analysis import snapshot
from daily539.backtest import run
from daily539.models import Draw
from daily539.source import _parse_record, _records
from daily539.strategy import select, valid_combo


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


def test_statistics_and_constraints():
    history = draws()
    assert sum(snapshot(history[-10:])["frequencies"].values()) == 50
    picks = select(history, seed=1)
    assert len(picks) == 2 and all(valid_combo(p, (60, 140)) for p in picks)
    assert len(set(picks[0]) & set(picks[1])) <= 2


def test_backtest_never_passes_current_draw(monkeypatch):
    history = draws(30)
    lengths = []
    monkeypatch.setattr("daily539.backtest.select", lambda prior, seed: lengths.append(len(prior)) or [(1, 2, 20, 21, 39)] * 2)
    _, _, rows = run(history, warmup=10)
    assert lengths == list(range(10, 30))
    assert len(rows) == 20

