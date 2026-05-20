from datetime import date

from sqlalchemy.orm import Session

from ...core.dependencies import get_owned_patient
from ...core.models import Doctor, Visit
from ...core.utils import optional_money


def create_visit(
    db: Session,
    doctor: Doctor,
    patient_id: int,
    visit_date: date | None = None,
    diagnosis: str | None = None,
    treatment: str | None = None,
    cost: str | None = None,
    paid: str | None = None,
) -> Visit:
    visit_date = visit_date or date.today()
    get_owned_patient(db, patient_id, doctor)
    visit = Visit(
        patient_id=patient_id,
        visit_date=visit_date,
        diagnosis=diagnosis,
        treatment=treatment,
        cost=optional_money(cost),
        paid=optional_money(paid),
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit
