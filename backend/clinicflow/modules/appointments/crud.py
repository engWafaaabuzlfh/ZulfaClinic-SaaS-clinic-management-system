from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...core.dependencies import get_owned_patient
from ...core.models import Appointment, AppointmentStatus, Doctor, Patient


def create_appointment(
    db: Session,
    doctor: Doctor,
    patient_id: int,
    appointment_date: date,
    appointment_time: str,
    reason: str | None = None,
) -> Appointment:
    get_owned_patient(db, patient_id, doctor)
    appointment = Appointment(
        patient_id=patient_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=reason,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(
    db: Session,
    doctor: Doctor,
    appointment_id: int,
    appointment_date: date,
    appointment_time: str,
    reason: str | None,
    status: AppointmentStatus,
) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if not appointment or appointment.patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appointment.appointment_date = appointment_date
    appointment.appointment_time = appointment_time
    appointment.reason = reason
    appointment.status = status
    db.commit()
    db.refresh(appointment)
    return appointment


def list_appointments(db: Session, doctor: Doctor, day: date | None = None) -> list[Appointment]:
    day = day or date.today()
    return (
        db.query(Appointment)
        .join(Patient)
        .filter(Appointment.appointment_date == day)
        .filter(Patient.doctor_id == doctor.id)
        .order_by(Appointment.appointment_time.asc())
        .all()
    )
