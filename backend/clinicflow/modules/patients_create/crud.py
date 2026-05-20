from sqlalchemy.orm import Session

from ...core.models import Doctor, Patient
from ...core.utils import optional_int


def create_patient(
    db: Session,
    doctor: Doctor,
    name: str,
    phone: str,
    age: str | None = None,
    notes: str | None = None,
) -> Patient:
    patient = Patient(
        doctor_id=doctor.id,
        name=name.strip(),
        phone=phone.strip(),
        age=optional_int(age),
        notes=notes,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
