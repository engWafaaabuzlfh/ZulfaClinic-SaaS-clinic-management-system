from typing import Annotated

from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor
from ...core.security import SESSION_COOKIE, sign_session

from . import crud
from .schemas import doctor_payload


router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/doctors")
def get_current_doctor(doctor: Annotated[Doctor, Depends(current_doctor)]):
    return doctor_payload(doctor)


@router.post("/doctors")
def create_doctor(
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    phone: Annotated[str | None, Form()] = None,
    specialty: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    password: Annotated[str, Form()] = "",
):
    doctor = crud.create_doctor(db, name, phone, password, specialty, notes)
    return doctor_payload(doctor)


@router.post("/auth/login")
def login(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    phone: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    doctor = crud.authenticate_doctor(db, phone, password)
    response.set_cookie(
        SESSION_COOKIE,
        sign_session(doctor.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return doctor_payload(doctor)


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}
