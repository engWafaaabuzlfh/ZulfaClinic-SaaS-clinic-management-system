from ...core.models import Appointment


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
