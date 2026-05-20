from typing import Annotated

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor

from . import crud
from .schemas import patient_payload


router = APIRouter(prefix="/api/patients", tags=["patients:create"])


@router.post("")
def create_patient(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    name: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    age: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
):
    patient = crud.create_patient(db, doctor, name, phone, age, notes)
    return patient_payload(patient)
