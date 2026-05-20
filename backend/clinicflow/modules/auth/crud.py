from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...core.models import Doctor
from ...core.security import hash_password, verify_password


def create_doctor(
    db: Session,
    name: str,
    phone: str | None,
    password: str,
    specialty: str | None = None,
    notes: str | None = None,
) -> Doctor:
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    existing = db.query(Doctor).filter(Doctor.phone == phone.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")

    doctor = Doctor(
        name=name.strip(),
        phone=phone.strip(),
        password_hash=hash_password(password),
        specialty=specialty,
        notes=notes,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def authenticate_doctor(db: Session, phone: str, password: str) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.phone == phone.strip()).first()
    if not doctor or not verify_password(password, doctor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    return doctor
