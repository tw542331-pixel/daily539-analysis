"""Replaceable draw sources; only Taiwan Lottery is enabled by default."""
from __future__ import annotations

import re
import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Draw


class DrawSource(ABC):
    @abstractmethod
    def fetch(self, start: date, end: date) -> list[Draw]: ...


class TaiwanLotterySource(DrawSource):
    """Adapter for the official Taiwan Lottery TLCAPIWeB endpoint.

    The URL can be replaced without changing analysis code because the official
    service has changed paths and response envelopes in the past.
    """

    DEFAULT_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result"

    def __init__(self, url: str = DEFAULT_URL, timeout: float = 30) -> None:
        self.url, self.timeout = url, timeout

    def fetch(self, start: date, end: date) -> list[Draw]:
        draws: dict[str, Draw] = {}
        cursor = date(start.year, start.month, 1)
        while cursor <= end:
            query = urlencode({"month": cursor.strftime("%Y-%m"), "pageNum": 1, "pageSize": 50})
            request = Request(f"{self.url}?{query}", headers={
                "Accept": "application/json", "User-Agent": "daily539-analysis/1.0"})
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
            for item in _records(payload):
                draw = _parse_record(item)
                if start <= draw.date <= end:
                    draws[draw.period] = draw
            cursor = date(cursor.year + (cursor.month == 12), cursor.month % 12 + 1, 1)
        return sorted(draws.values())


def _records(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("unexpected official response")
    for key in ("daily539Res", "content", "data", "result", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _records(value)
            if nested:
                return nested
    return []


def _parse_record(item: dict[str, Any]) -> Draw:
    period = str(item.get("drawTerm") or item.get("period") or item.get("drawNumber") or "")
    raw_date = item.get("drawDate") or item.get("date") or item.get("lotteryDate")
    if not raw_date:
        raise ValueError("official record has no draw date")
    day = _parse_date(str(raw_date))
    raw_numbers = item.get("drawNumberSize") or item.get("drawNumbers") or item.get("numbers")
    if isinstance(raw_numbers, str):
        numbers = [int(value) for value in re.findall(r"\d+", raw_numbers)]
    elif isinstance(raw_numbers, list):
        numbers = [int(value) for value in raw_numbers]
    else:
        numbers = [int(item[key]) for key in sorted(item) if re.fullmatch(r"drawNumber\d+", key)]
    return Draw(day, period or day.isoformat(), tuple(sorted(numbers[:5])))


def _parse_date(value: str) -> date:
    value = value.split("T", 1)[0].replace("/", "-")
    parts = value.split("-")
    if len(parts) == 3 and int(parts[0]) < 1911:  # ROC calendar
        value = f"{int(parts[0]) + 1911:04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    return datetime.strptime(value, "%Y-%m-%d").date()
