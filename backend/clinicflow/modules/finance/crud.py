from datetime import date

from sqlalchemy.orm import Session

from ...core.models import Doctor, Patient, Visit


def list_finance_visits(db: Session, doctor: Doctor, day: date | None = None) -> list[Visit]:
    query = db.query(Visit).join(Patient).filter(Patient.doctor_id == doctor.id)
    if day:
        query = query.filter(Visit.visit_date == day)
    return query.order_by(Visit.visit_date.desc(), Visit.id.desc()).limit(120).all()
