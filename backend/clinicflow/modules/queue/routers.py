from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor, QueueStatus

from . import crud
from .schemas import queue_payload


router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.post("")
def add_to_queue(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    patient_id: Annotated[int, Form()],
    queue_date: Annotated[date | None, Form()] = None,
):
    return queue_payload(crud.add_to_queue(db, doctor, patient_id, queue_date))


@router.get("")
def list_queue(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    return [queue_payload(entry) for entry in crud.list_queue(db, doctor, day)]


@router.put("/{entry_id}")
def update_queue_status(
    entry_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    status: Annotated[QueueStatus, Form()],
):
    return queue_payload(crud.update_queue_status(db, doctor, entry_id, status))
