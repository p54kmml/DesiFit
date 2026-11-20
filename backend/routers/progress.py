from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, BodyMeasurement, UserProfile
from backend.schemas import BodyMeasurementCreate, BodyMeasurementResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/progress", tags=["Body Progress"])


@router.get("/measurements", response_model=List[BodyMeasurementResponse])
def get_measurements(
    limit: Optional[int] = Query(30, description="Max number of records"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch the newest N records, then return them oldest-to-newest so charts
    # remain chronological without silently omitting recent progress.
    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == current_user.id)
        .order_by(BodyMeasurement.date.desc(), BodyMeasurement.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(measurements))


@router.post("/measurements", response_model=BodyMeasurementResponse, status_code=status.HTTP_201_CREATED)
def record_measurement(
    measurement_in: BodyMeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meas_date = measurement_in.date or date.today()

    measurement = BodyMeasurement(
        user_id=current_user.id,
        weight_kg=measurement_in.weight_kg,
        chest_cm=measurement_in.chest_cm,
        waist_cm=measurement_in.waist_cm,
        arm_cm=measurement_in.arm_cm,
        thigh_cm=measurement_in.thigh_cm,
        notes=measurement_in.notes,
        date=meas_date
    )
    db.add(measurement)

    # Automatically keep profile current_weight_kg in sync
    profile = current_user.profile
    if profile:
        profile.current_weight_kg = measurement_in.weight_kg

    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/measurements/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    measurement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meas = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.id == measurement_id, BodyMeasurement.user_id == current_user.id)
        .first()
    )
    if not meas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement record not found")
    db.delete(meas)
    db.commit()
    return None
