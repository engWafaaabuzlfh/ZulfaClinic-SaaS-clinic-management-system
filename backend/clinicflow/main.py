import base64
import hashlib
import hmac
import os
import secrets
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, or_, text
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Appointment, AppointmentStatus, Doctor, Patient, QueueEntry, QueueStatus, Visit


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Zulfa Clinic")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR / "templates")
SESSION_SECRET = os.getenv("SESSION_SECRET", "clinicflow-dev-secret-change-me")
SESSION_COOKIE = "clinicflow_session"


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema()


def ensure_schema() -> None:
    inspector = inspect(engine)
    if "patients" not in inspector.get_table_names():
        return

    patient_columns = {column["name"] for column in inspector.get_columns("patients")}
    doctor_columns = {column["name"] for column in inspector.get_columns("doctors")}
    if "password_hash" not in doctor_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE doctors ADD COLUMN password_hash VARCHAR(220) NULL"))
    if "doctor_id" not in patient_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE patients ADD COLUMN doctor_id INTEGER NULL"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_patients_doctor_id ON patients (doctor_id)"))
            connection.execute(
                text(
                    "ALTER TABLE patients "
                    "ADD CONSTRAINT fk_patients_doctor_id "
                    "FOREIGN KEY (doctor_id) REFERENCES doctors(id)"
                )
            )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash or "$" not in password_hash:
        return False
    salt, stored = password_hash.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return hmac.compare_digest(base64.b64encode(digest).decode(), stored)


def sign_session(doctor_id: int) -> str:
    value = str(doctor_id)
    signature = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def read_session(value: str | None) -> int | None:
    if not value or "." not in value:
        return None
    doctor_id, signature = value.split(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), doctor_id.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    return int(doctor_id) if doctor_id.isdigit() else None


def current_doctor_optional(
    db: Annotated[Session, Depends(get_db)],
    session_cookie: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> Doctor | None:
    doctor_id = read_session(session_cookie)
    return db.get(Doctor, doctor_id) if doctor_id else None


def current_doctor(
    doctor: Annotated[Doctor | None, Depends(current_doctor_optional)],
) -> Doctor:
    if not doctor:
        raise HTTPException(status_code=401, detail="Login required")
    return doctor


def page_context(request: Request, page: str, doctor: Doctor | None, **extra):
    if not doctor and page not in {"login", "register"}:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "page": page, "doctor": doctor, **extra},
    )


@app.get("/", response_class=HTMLResponse)
def index(doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return RedirectResponse("/patients" if doctor else "/login")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    if doctor:
        return RedirectResponse("/patients")
    return page_context(request, "login", doctor)


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    if doctor:
        return RedirectResponse("/patients")
    return page_context(request, "register", doctor)


@app.get("/patients", response_class=HTMLResponse)
def patients_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return page_context(request, "patients", doctor)


@app.get("/patients/new", response_class=HTMLResponse)
def new_patient_page(request: Request, doctor: Annotated[Doctor | None, Depends(current_doctor_optional)]):
    return page_context(request, "new-patient", doctor)


@app.get("/doctors", response_class=HTMLResponse)
def doctors_page():
    return RedirectResponse("/register")


@app.get("/patients/{patient_id}", response_class=HTMLResponse)
def patient_page(
    patient_id: int,
    request: Request,
    doctor: Annotated[Doctor | None, Depends(current_doctor_optional)],
):
    return page_context(request, "patient", doctor, patient_id=patient_id)


def patient_payload(patient: Patient) -> dict:
    return {
        "id": patient.id,
        "doctor_id": patient.doctor_id,
        "doctor_name": patient.doctor.name if patient.doctor else "",
        "name": patient.name,
        "phone": patient.phone,
        "age": patient.age,
        "notes": patient.notes or "",
    }


def doctor_payload(doctor: Doctor) -> dict:
    return {
        "id": doctor.id,
        "name": doctor.name,
        "phone": doctor.phone or "",
        "specialty": doctor.specialty or "",
        "notes": doctor.notes or "",
        "patients_count": len(doctor.patients),
    }


def get_owned_patient(db: Session, patient_id: int, doctor: Doctor) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient or patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def optional_int(value: str | int | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def optional_money(value: str | float | None) -> float:
    if value in (None, ""):
        return 0
    return float(value)


def appointment_payload(appointment: Appointment) -> dict:
    return {
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": appointment.patient.name,
        "phone": appointment.patient.phone,
        "date": appointment.appointment_date.isoformat(),
        "time": appointment.appointment_time,
        "reason": appointment.reason or "",
        "status": appointment.status.value,
    }


def queue_payload(entry: QueueEntry) -> dict:
    return {
        "id": entry.id,
        "patient_id": entry.patient_id,
        "patient_name": entry.patient.name,
        "phone": entry.patient.phone,
        "status": entry.status.value,
        "created_at": entry.created_at.strftime("%H:%M"),
    }


def visit_payload(visit: Visit) -> dict:
    cost = Decimal(visit.cost or 0)
    paid = Decimal(visit.paid or 0)
    return {
        "id": visit.id,
        "patient_id": visit.patient_id,
        "patient_name": visit.patient.name,
        "date": visit.visit_date.isoformat(),
        "diagnosis": visit.diagnosis or "",
        "treatment": visit.treatment or "",
        "cost": float(cost),
        "paid": float(paid),
        "remaining": float(cost - paid),
    }


def patient_table_payload(patient: Patient, db: Session) -> dict:
    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient.id)
        .order_by(Visit.visit_date.desc(), Visit.id.desc())
        .all()
    )
    next_appointment = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient.id,
            Appointment.status == AppointmentStatus.scheduled,
            Appointment.appointment_date >= date.today(),
        )
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .first()
    )
    total_cost = sum(Decimal(visit.cost or 0) for visit in visits)
    total_paid = sum(Decimal(visit.paid or 0) for visit in visits)

    return {
        **patient_payload(patient),
        "last_visit": visits[0].visit_date.isoformat() if visits else "",
        "next_appointment": (
            f"{next_appointment.appointment_date.isoformat()} {next_appointment.appointment_time}"
            if next_appointment
            else ""
        ),
        "total_cost": float(total_cost),
        "total_paid": float(total_paid),
        "total_remaining": float(total_cost - total_paid),
    }


@app.get("/api/patients")
def list_patients(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    q: str = "",
):
    query = db.query(Patient).filter(Patient.doctor_id == doctor.id).order_by(Patient.created_at.desc())
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(Patient.name.ilike(like), Patient.phone.ilike(like)))
    return [patient_table_payload(patient, db) for patient in query.limit(120).all()]


@app.post("/api/patients")
def create_patient(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    name: Annotated[str, Form()],
    phone: Annotated[str, Form()],
    age: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
):
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
    return patient_payload(patient)


@app.get("/api/doctors")
def get_current_doctor(doctor: Annotated[Doctor, Depends(current_doctor)]):
    return doctor_payload(doctor)


@app.post("/api/doctors")
def create_doctor(
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    phone: Annotated[str | None, Form()] = None,
    specialty: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    password: Annotated[str, Form()] = "",
):
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    existing = db.query(Doctor).filter(Doctor.phone == phone.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    doctor = Doctor(
        name=name.strip(),
        phone=phone.strip(),
        password_hash=hash_password(password),
        specialty=specialty,
        notes=notes,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor_payload(doctor)


@app.post("/api/auth/login")
def login(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    phone: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    doctor = db.query(Doctor).filter(Doctor.phone == phone.strip()).first()
    if not doctor or not verify_password(password, doctor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password")
    response.set_cookie(
        SESSION_COOKIE,
        sign_session(doctor.id),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 14,
    )
    return doctor_payload(doctor)


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/patients/{patient_id}")
def get_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    patient = db.get(Patient, patient_id)
    if not patient or patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    visits = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id)
        .order_by(Visit.visit_date.desc(), Visit.id.desc())
        .all()
    )
    appointments = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )
    visit_rows = [visit_payload(visit) for visit in visits]
    return {
        **patient_payload(patient),
        "appointments": [appointment_payload(appointment) for appointment in appointments],
        "visits": visit_rows,
        "total_cost": sum(row["cost"] for row in visit_rows),
        "total_paid": sum(row["paid"] for row in visit_rows),
        "total_remaining": sum(row["remaining"] for row in visit_rows),
    }


@app.delete("/api/patients/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    patient = get_owned_patient(db, patient_id, doctor)
    db.delete(patient)
    db.commit()
    return {"ok": True}


@app.put("/api/patients/{patient_id}/doctor")
def update_patient_doctor(
    patient_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
):
    patient = db.get(Patient, patient_id)
    if not patient or patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.doctor_id = doctor.id
    db.commit()
    db.refresh(patient)
    return patient_payload(patient)


@app.post("/api/appointments")
def create_appointment(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    patient_id: Annotated[int, Form()],
    appointment_date: Annotated[date, Form()],
    appointment_time: Annotated[str, Form()],
    reason: Annotated[str | None, Form()] = None,
):
    get_owned_patient(db, patient_id, doctor)
    appointment = Appointment(
        patient_id=patient_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        reason=reason,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment_payload(appointment)


@app.put("/api/appointments/{appointment_id}")
def update_appointment(
    appointment_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    appointment_date: Annotated[date, Form()],
    appointment_time: Annotated[str, Form()],
    reason: Annotated[str | None, Form()] = None,
    status: Annotated[AppointmentStatus, Form()] = AppointmentStatus.scheduled,
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment or appointment.patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appointment.appointment_date = appointment_date
    appointment.appointment_time = appointment_time
    appointment.reason = reason
    appointment.status = status
    db.commit()
    db.refresh(appointment)
    return appointment_payload(appointment)


@app.get("/api/appointments")
def list_appointments(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    day = day or date.today()
    appointments = (
        db.query(Appointment)
        .join(Patient)
        .filter(Appointment.appointment_date == day)
        .filter(Patient.doctor_id == doctor.id)
        .order_by(Appointment.appointment_time.asc())
        .all()
    )
    return [appointment_payload(appointment) for appointment in appointments]


@app.post("/api/queue")
def add_to_queue(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    patient_id: Annotated[int, Form()],
    queue_date: Annotated[date | None, Form()] = None,
):
    queue_date = queue_date or date.today()
    get_owned_patient(db, patient_id, doctor)
    entry = QueueEntry(patient_id=patient_id, queue_date=queue_date)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return queue_payload(entry)


@app.get("/api/queue")
def list_queue(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    day = day or date.today()
    entries = (
        db.query(QueueEntry)
        .join(Patient)
        .filter(QueueEntry.queue_date == day)
        .filter(Patient.doctor_id == doctor.id)
        .order_by(QueueEntry.created_at.asc())
        .all()
    )
    return [queue_payload(entry) for entry in entries]


@app.put("/api/queue/{entry_id}")
def update_queue_status(
    entry_id: int,
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    status: Annotated[QueueStatus, Form()],
):
    entry = db.get(QueueEntry, entry_id)
    if not entry or entry.patient.doctor_id != doctor.id:
        raise HTTPException(status_code=404, detail="Queue entry not found")
    entry.status = status
    db.commit()
    db.refresh(entry)
    return queue_payload(entry)


@app.post("/api/visits")
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
    return visit_payload(visit)


@app.get("/api/finance")
def finance_summary(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    query = db.query(Visit).join(Patient).filter(Patient.doctor_id == doctor.id)
    if day:
        query = query.filter(Visit.visit_date == day)
    visits = query.order_by(Visit.visit_date.desc(), Visit.id.desc()).limit(120).all()
    rows = [visit_payload(visit) for visit in visits]
    return {
        "rows": rows,
        "total_cost": sum(row["cost"] for row in rows),
        "total_paid": sum(row["paid"] for row in rows),
        "total_remaining": sum(row["remaining"] for row in rows),
    }
