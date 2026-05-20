from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor

from . import crud
from .schemas import patient_detail_payload, patient_payload, patient_table_payload


router = APIRouter(prefix="/api/patients", tags=["patients:get"])


@router.get("")
def list_patients(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    q: str = "",
):
    patients = crud.list_patients(db, doctor, q)
    return [patient_table_payload(patient, db) for patient in patients]


@router.get("/{patient_id}")
def get_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    patient, visits, appointments = crud.get_patient_detail(db, patient_id, doctor)
    return patient_detail_payload(patient, visits, appointments)


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    crud.delete_patient(db, patient_id, doctor)
    return {"ok": True}


@router.put("/{patient_id}/doctor")
def update_patient_doctor(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    patient = crud.reassign_to_current_doctor(db, patient_id, doctor)
    return patient_payload(patient)
