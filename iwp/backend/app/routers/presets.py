from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/presets", tags=["presets"])


@router.get("", response_model=list[schemas.WeightPresetOut])
def list_presets(db: Session = Depends(get_db)):
    return db.query(models.WeightPreset).all()


@router.post("", response_model=schemas.WeightPresetOut)
def create_preset(payload: schemas.WeightPresetIn, db: Session = Depends(get_db)):
    if db.query(models.WeightPreset).filter_by(name=payload.name).first():
        raise HTTPException(400, "A preset with this name already exists.")
    if payload.min_weight > payload.max_weight:
        raise HTTPException(400, "min_weight cannot be greater than max_weight.")
    preset = models.WeightPreset(**payload.model_dump())
    db.add(preset)
    db.commit()
    db.refresh(preset)
    return preset


@router.put("/{preset_id}", response_model=schemas.WeightPresetOut)
def update_preset(preset_id: int, payload: schemas.WeightPresetIn, db: Session = Depends(get_db)):
    preset = db.get(models.WeightPreset, preset_id)
    if not preset:
        raise HTTPException(404, "Preset not found.")
    for k, v in payload.model_dump().items():
        setattr(preset, k, v)
    db.commit()
    db.refresh(preset)
    return preset


@router.delete("/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.get(models.WeightPreset, preset_id)
    if not preset:
        raise HTTPException(404, "Preset not found.")
    db.delete(preset)
    db.commit()
    return {"status": "deleted"}
