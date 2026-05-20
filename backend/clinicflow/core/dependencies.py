from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import Doctor, Patient
from .security import SESSION_COOKIE, read_session


def current_doctor_optional(
    db: Annotated[Session, Depends(get_db)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Doctor | None:
    doctor_id = read_session(session_cookie)
    return db.get(Doctor, doctor_id) if doctor_id else None


def current_doctor(
    doctor: Annotated[Doctor | None, Depends(current_doctor_optional)],
) -> Doctor:
    if not doctor:
        raise HTTPException(status_code=401, detail="Login required")
    return doctor


def get_owned_patient(db: Session, patient_id: int, doctor: Doctor) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient or patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
