from ...core.models import Doctor


def doctor_payload(doctor: Doctor) -> dict:
    return {
        "id": doctor.id,
        "name": doctor.name,
        "phone": doctor.phone or "",
        "specialty": doctor.specialty or "",
        "notes": doctor.notes or "",
        "patients_count": len(doctor.patients),
    }
