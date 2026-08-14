"""
Public read-only lookup endpoint. This is what your separate lookup webapp
(the one you're building for anyone to enter a Box ID and see its record)
should call. No auth by default since you described it as a public
traceability check - add an API key dependency here later if you decide it
needs to be restricted.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/lookup", tags=["lookup"])


@router.get("/{box_id}", response_model=schemas.BoxRecordOut)
def lookup_box(box_id: str, db: Session = Depends(get_db)):
    record = db.query(models.BoxRecord).filter_by(box_id=box_id.strip().upper()).first()
    if not record:
        raise HTTPException(404, f"No record found for box ID '{box_id}'.")
    return record
