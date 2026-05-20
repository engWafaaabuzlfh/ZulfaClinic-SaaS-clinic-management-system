from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...core.dependencies import get_owned_patient
from ...core.models import Appointment, Doctor, Patient, Visit


def list_patients(db: Session, doctor: Doctor, q: str = "") -> list[Patient]:
    query = db.query(Patient).filter(Patient.doctor_id == doctor.id).order_by(Patient.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Patient.name.ilike(like), Patient.phone.ilike(like)))
    return query.limit(120).all()


def get_patient_detail(db: Session, patient_id: int, doctor: Doctor) -> tuple[Patient, list[Visit], list[Appointment]]:
    patient = get_owned_patient(db, patient_id, doctor)
    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id)
        .order_by(Visit.visit_date.desc(), Visit.id.desc())
        .all()
    )
    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )
    return patient, visits, appointments


def delete_patient(db: Session, patient_id: int, doctor: Doctor) -> None:
    patient = get_owned_patient(db, patient_id, doctor)
    db.delete(patient)
    db.commit()


def reassign_to_current_doctor(db: Session, patient_id: int, doctor: Doctor) -> Patient:
    patient = get_owned_patient(db, patient_id, doctor)
    patient.doctor_id = doctor.id
    db.commit()
    db.refresh(patient)
    return patient
