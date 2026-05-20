from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...core.dependencies import get_owned_patient
from ...core.models import Doctor, Patient, QueueEntry, QueueStatus


def add_to_queue(db: Session, doctor: Doctor, patient_id: int, queue_date: date | None = None) -> QueueEntry:
    queue_date = queue_date or date.today()
    get_owned_patient(db, patient_id, doctor)
    entry = QueueEntry(patient_id=patient_id, queue_date=queue_date)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_queue(db: Session, doctor: Doctor, day: date | None = None) -> list[QueueEntry]:
    day = day or date.today()
    return (
        db.query(QueueEntry)
        .join(Patient)
        .filter(QueueEntry.queue_date == day)
        .filter(Patient.doctor_id == doctor.id)
        .order_by(QueueEntry.created_at.asc())
        .all()
    )


def update_queue_status(db: Session, doctor: Doctor, entry_id: int, status: QueueStatus) -> QueueEntry:
    entry = db.get(QueueEntry, entry_id)
    if not entry or entry.patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Queue entry not found")
    entry.status = status
    db.commit()
    db.refresh(entry)
    return entry
