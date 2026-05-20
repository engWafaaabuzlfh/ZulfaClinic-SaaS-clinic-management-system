from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from ...core.models import Appointment, AppointmentStatus, Patient, Visit
from ...modules.appointments.schemas import appointment_payload
from ...modules.visits.schemas import visit_payload


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


def patient_detail_payload(patient: Patient, visits: list[Visit], appointments: list[Appointment]) -> dict:
    visit_rows = [visit_payload(visit) for visit in visits]
    return {
        **patient_payload(patient),
        "appointments": [appointment_payload(appointment) for appointment in appointments],
        "visits": visit_rows,
        "total_cost": sum(row["cost"] for row in visit_rows),
        "total_paid": sum(row["paid"] for row in visit_rows),
        "total_remaining": sum(row["remaining"] for row in visit_rows),
    }
