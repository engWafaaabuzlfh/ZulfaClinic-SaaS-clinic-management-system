from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import AppointmentStatus, Doctor

from . import crud
from .schemas import appointment_payload


router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("")
def create_appointment(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    patient_id: Annotated[int, Form()],
    appointment_date: Annotated[date, Form()],
    appointment_time: Annotated[str, Form()],
    reason: Annotated[str | None, Form()] = None,
):
    appointment = crud.create_appointment(db, doctor, patient_id, appointment_date, appointment_time, reason)
    return appointment_payload(appointment)


@router.put("/{appointment_id}")
def update_appointment(
    appointment_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    appointment_date: Annotated[date, Form()],
    appointment_time: Annotated[str, Form()],
    reason: Annotated[str | None, Form()] = None,
    status: Annotated[AppointmentStatus, Form()] = AppointmentStatus.scheduled,
):
    appointment = crud.update_appointment(db, doctor, appointment_id, appointment_date, appointment_time, reason, status)
    return appointment_payload(appointment)


@router.get("")
def list_appointments(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    return [appointment_payload(appointment) for appointment in crud.list_appointments(db, doctor, day)]
