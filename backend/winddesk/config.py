"""Static domain configuration and runtime settings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict

UK_TZ = ZoneInfo("Europe/London")

AuctionId = Literal["epex_60", "n2ex_60", "epex_30"]


@dataclass(frozen=True)
class Auction:
    id: AuctionId
    label: str
    venue: str
    gate_closure: time  # UK local time on the day before delivery
    product_minutes: int


AUCTIONS: dict[AuctionId, Auction] = {
    "epex_60": Auction("epex_60", "EPEX GB Day-Ahead 60-min", "EPEX SPOT", time(9, 20), 60),
    "n2ex_60": Auction("n2ex_60", "N2EX GB Day-Ahead hourly", "Nord Pool", time(9, 50), 60),
    "epex_30": Auction("epex_30", "EPEX GB Day-Ahead 30-min", "EPEX SPOT", time(15, 30), 30),
}
DEFAULT_AUCTION_ID: AuctionId = "epex_60"

# Purchase decisions made in January 2026 = auctions held 1-31 January,
# i.e. delivery days 2 January - 1 February 2026.
FIRST_DELIVERY_DAY = date(2026, 1, 2)
LAST_DELIVERY_DAY = date(2026, 2, 1)

MAX_LEAD_HOURS = 48

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WINDDESK_")

    data_dir: Path = _REPO_ROOT / "data" / "snapshot"
    static_dir: Path | None = None  # built frontend; served by the API when set
    log_level: str = "INFO"
