from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor

from . import crud
from .schemas import visit_payload


router = APIRouter(prefix="/api/visits", tags=["visits"])


@router.post("")
def create_visit(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    patient_id: Annotated[int, Form()],
    visit_date: Annotated[date | None, Form()] = None,
    diagnosis: Annotated[str | None, Form()] = None,
    treatment: Annotated[str | None, Form()] = None,
    cost: Annotated[str | None, Form()] = None,
    paid: Annotated[str | None, Form()] = None,
):
    visit = crud.create_visit(db, doctor, patient_id, visit_date, diagnosis, treatment, cost, paid)
    return visit_payload(visit)
