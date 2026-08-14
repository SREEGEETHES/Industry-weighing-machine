import datetime as dt
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("", response_model=list[schemas.BoxRecordOut])
def list_records(
    db: Session = Depends(get_db),
    station_id: int | None = None,
    print_status: str | None = None,
    within_tolerance: bool | None = None,
    date_from: dt.date | None = None,
    date_to: dt.date | None = None,
    limit: int = Query(200, le=2000),
):
    q = db.query(models.BoxRecord)
    if station_id is not None:
        q = q.filter(models.BoxRecord.station_id == station_id)
    if print_status is not None:
        q = q.filter(models.BoxRecord.print_status == print_status)
    if within_tolerance is not None:
        q = q.filter(models.BoxRecord.within_tolerance == within_tolerance)
    if date_from is not None:
        q = q.filter(models.BoxRecord.created_at >= dt.datetime.combine(date_from, dt.time.min))
    if date_to is not None:
        q = q.filter(models.BoxRecord.created_at <= dt.datetime.combine(date_to, dt.time.max))
    return q.order_by(models.BoxRecord.created_at.desc()).limit(limit).all()
