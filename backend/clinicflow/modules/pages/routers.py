from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ...core.dependencies import current_doctor_optional
from ...core.models import Doctor


FRONTEND_DIR = Path(__file__).resolve().parents[4] / "frontend"
templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")
router = APIRouter(tags=["pages"])


def page_context(request: Request, page: str, doctor: Doctor | None, **extra):
    if not doctor and page not in {"login", "register"}:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "page": page, "doctor": doctor, **extra},
    )


@router.get("/", response_class=HTMLResponse)
def index(doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return RedirectResponse("/patients" if doctor else "/login")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    if doctor:
        return RedirectResponse("/patients")
    return page_context(request, "login", doctor)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    if doctor:
        return RedirectResponse("/patients")
    return page_context(request, "register", doctor)


@router.get("/patients", response_class=HTMLResponse)
def patients_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return page_context(request, "patients", doctor)


@router.get("/patients/new", response_class=HTMLResponse)
def new_patient_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return page_context(request, "new-patient", doctor)


@router.get("/doctors", response_class=HTMLResponse)
def doctors_page():
    return RedirectResponse("/register")


@router.get("/patients/{patient_id}", response_class=HTMLResponse)
def patient_page(
    patient_id: int,
    request: Request,
    doctor: Annotated[Doctor | None, Depends(current_doctor_optional)],
):
    return page_context(request, "patient", doctor, patient_id=patient_id)
