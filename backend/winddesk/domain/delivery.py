"""Delivery-day windows and auction decision cutoffs (GB day-ahead conventions).

GB day-ahead auctions trade the EFA day: delivery day D runs from 23:00 UK time on D-1
to 23:00 UK time on D (23 or 25 hours on clock-change days).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from winddesk.config import UK_TZ, Auction

DELIVERY_DAY_START = time(23, 0)


def delivery_window(day: date) -> tuple[datetime, datetime]:
    """UTC [start, end) of delivery day `day`."""
    start = datetime.combine(day - timedelta(days=1), DELIVERY_DAY_START, tzinfo=UK_TZ)
    end = datetime.combine(day, DELIVERY_DAY_START, tzinfo=UK_TZ)
    return start.astimezone(UTC), end.astimezone(UTC)


def decision_cutoff(day: date, auction: Auction) -> datetime:
    """UTC instant of the auction's gate closure on D-1 for delivery day `day`."""
    local = datetime.combine(day - timedelta(days=1), auction.gate_closure, tzinfo=UK_TZ)
    return local.astimezone(UTC)


def delivery_days(first: date, last: date) -> list[date]:
    """All delivery days from `first` to `last`, inclusive."""
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def delivery_day_of(ts: datetime) -> date:
    """The delivery day containing instant `ts` (timezone-aware)."""
    local = ts.astimezone(UK_TZ)
    if local.time() >= DELIVERY_DAY_START:
        return local.date() + timedelta(days=1)
    return local.date()
