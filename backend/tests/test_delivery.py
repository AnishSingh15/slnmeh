from datetime import UTC, date, datetime, timedelta
from typing import get_args

import pytest

from winddesk.config import AUCTIONS, AuctionId
from winddesk.domain.delivery import (
    decision_cutoff,
    delivery_day_of,
    delivery_days,
    delivery_window,
)


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def test_delivery_window_is_efa_day_in_winter() -> None:
    assert delivery_window(date(2026, 1, 12)) == (utc(2026, 1, 11, 23), utc(2026, 1, 12, 23))


def test_spring_clock_change_day_is_23_hours() -> None:
    start, end = delivery_window(date(2026, 3, 29))
    assert start == utc(2026, 3, 28, 23)
    assert end == utc(2026, 3, 29, 22)
    assert end - start == timedelta(hours=23)


def test_autumn_clock_change_day_is_25_hours() -> None:
    start, end = delivery_window(date(2026, 10, 25))
    assert start == utc(2026, 10, 24, 22)
    assert end - start == timedelta(hours=25)


@pytest.mark.parametrize(
    ("auction_id", "expected"),
    [
        ("epex_60", utc(2026, 1, 11, 9, 20)),
        ("n2ex_60", utc(2026, 1, 11, 9, 50)),
        ("epex_30", utc(2026, 1, 11, 15, 30)),
    ],
)
def test_decision_cutoff_is_gate_closure_on_previous_day(
    auction_id: AuctionId, expected: datetime
) -> None:
    assert decision_cutoff(date(2026, 1, 12), AUCTIONS[auction_id]) == expected


def test_decision_cutoff_in_summer_converts_bst_to_utc() -> None:
    assert decision_cutoff(date(2026, 7, 1), AUCTIONS["epex_60"]) == utc(2026, 6, 30, 8, 20)


def test_delivery_day_of_maps_23_00_uk_to_next_day() -> None:
    assert delivery_day_of(utc(2026, 1, 11, 23)) == date(2026, 1, 12)
    assert delivery_day_of(utc(2026, 1, 11, 22)) == date(2026, 1, 11)
    assert delivery_day_of(utc(2026, 6, 30, 22)) == date(2026, 7, 1)  # 23:00 BST


def test_delivery_days_is_inclusive() -> None:
    days = delivery_days(date(2026, 1, 2), date(2026, 2, 1))
    assert len(days) == 31
    assert (days[0], days[-1]) == (date(2026, 1, 2), date(2026, 2, 1))


def test_auction_ids_match_literal() -> None:
    assert set(AUCTIONS) == set(get_args(AuctionId))
