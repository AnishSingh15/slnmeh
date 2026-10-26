"""Pins headline numbers on the committed snapshot to values from an independently
written prototype (computed while designing, before this code existed)."""

from pathlib import Path

import pytest

from winddesk.repository import load_snapshot
from winddesk.service import WindDeskService

SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshot"


@pytest.fixture(scope="module")
def real() -> WindDeskService:
    if not (SNAPSHOT_DIR / "manifest.json").exists():
        pytest.skip("snapshot not present")
    return WindDeskService(load_snapshot(SNAPSHOT_DIR))


def test_pilot_window_is_744_complete_hours(real: WindDeskService) -> None:
    assert real.accuracy("epex_60").raw.n == 744


def test_epex_60_uses_the_0730_run_every_day(real: WindDeskService) -> None:
    published = real.datasets["epex_60"].hours["publish_time"]
    assert (published.dt.strftime("%H:%M") == "07:30").all()


def test_headline_numbers(real: WindDeskService) -> None:
    acc = real.accuracy("epex_60")
    assert acc.raw.mae_mw == pytest.approx(2035, abs=1.5)
    assert acc.raw.rmse_mw == pytest.approx(2498, abs=1.5)
    assert acc.raw.bias_mw == pytest.approx(1749, abs=1.5)
    assert acc.raw.share_over_forecast == pytest.approx(0.852, abs=0.002)
    assert acc.calibrated.mae_mw == pytest.approx(1209, rel=0.01)
    assert acc.band_coverage == pytest.approx(0.784, abs=0.01)


@pytest.mark.parametrize(("auction_id", "mae"), [("n2ex_60", 2008), ("epex_30", 1876)])
def test_other_auctions(real: WindDeskService, auction_id: str, mae: float) -> None:
    assert real.accuracy(auction_id).raw.mae_mw == pytest.approx(mae, abs=1.5)  # type: ignore[arg-type]
