"""
Generates sequential Box IDs in the exact format you specified:
BOX-2026-000001

The sequence resets each calendar year (matching the `year` field already
in BoxRecord) and is derived from the actual max sequence_number stored in
the DB for that year - not an in-memory counter - so it survives restarts
and stays correct even with multiple stations writing concurrently
(guarded by the DB transaction in weighing_service).
"""
import datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import BoxRecord
from app.config import BOX_ID_PREFIX


def generate_box_id(db: Session) -> tuple[str, int, int]:
    year = dt.datetime.utcnow().year
    max_seq = (
        db.query(func.max(BoxRecord.sequence_number))
        .filter(BoxRecord.year == year)
        .scalar()
    )
    next_seq = (max_seq or 0) + 1
    box_id = f"{BOX_ID_PREFIX}-{year}-{next_seq:06d}"
    return box_id, next_seq, year
