from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/recipients", tags=["recipients"])


@router.get("", response_model=list[schemas.EmailRecipientOut])
def list_recipients(db: Session = Depends(get_db)):
    return db.query(models.EmailRecipient).all()


@router.post("", response_model=schemas.EmailRecipientOut)
def add_recipient(payload: schemas.EmailRecipientIn, db: Session = Depends(get_db)):
    if db.query(models.EmailRecipient).filter_by(email=payload.email).first():
        raise HTTPException(400, "This email is already in the recipient list.")
    recipient = models.EmailRecipient(**payload.model_dump())
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.put("/{recipient_id}", response_model=schemas.EmailRecipientOut)
def update_recipient(recipient_id: int, payload: schemas.EmailRecipientIn, db: Session = Depends(get_db)):
    recipient = db.get(models.EmailRecipient, recipient_id)
    if not recipient:
        raise HTTPException(404, "Recipient not found.")
    for k, v in payload.model_dump().items():
        setattr(recipient, k, v)
    db.commit()
    db.refresh(recipient)
    return recipient


@router.delete("/{recipient_id}")
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient = db.get(models.EmailRecipient, recipient_id)
    if not recipient:
        raise HTTPException(404, "Recipient not found.")
    db.delete(recipient)
    db.commit()
    return {"status": "deleted"}
