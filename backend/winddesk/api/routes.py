"""HTTP routes. Parameter validation lives here; computation lives in the service."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from winddesk.api import schemas as s
from winddesk.config import DEFAULT_AUCTION_ID, MAX_LEAD_HOURS, AuctionId
from winddesk.service import OutOfWindowError, WindDeskService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> WindDeskService:
    service: WindDeskService = request.app.state.service
    return service


Service = Annotated[WindDeskService, Depends(get_service)]
AuctionParam = Annotated[
    AuctionId, Query(description="Auction whose gate closure is the decision cutoff")
]


@router.get("/health")
def health(service: Service) -> s.HealthResponse:
    return service.health()


@router.get("/meta")
def meta(service: Service) -> s.MetaResponse:
    return service.meta()


@router.get("/delivery-day")
def delivery_day(
    service: Service,
    day: Annotated[date, Query(alias="date", description="Delivery day (YYYY-MM-DD)")],
    auction: AuctionParam = DEFAULT_AUCTION_ID,
) -> s.DeliveryDayResponse:
    try:
        return service.delivery_day(day, auction)
    except OutOfWindowError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/accuracy")
def accuracy(service: Service, auction: AuctionParam = DEFAULT_AUCTION_ID) -> s.AccuracyResponse:
    return service.accuracy(auction)


@router.get("/lead-time")
def lead_time(
    service: Service,
    hours: Annotated[int, Query(ge=0, le=MAX_LEAD_HOURS, description="Minimum lead time")] = 4,
    start: Annotated[date | None, Query(description="First delivery day")] = None,
    end: Annotated[date | None, Query(description="Last delivery day")] = None,
) -> s.LeadTimeResponse:
    try:
        return service.lead_time(start or service.days[0], end or service.days[-1], hours)
    except OutOfWindowError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
