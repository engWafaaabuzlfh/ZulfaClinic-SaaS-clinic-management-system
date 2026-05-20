from ...core.models import QueueEntry


def queue_payload(entry: QueueEntry) -> dict:
    return {
        "id": entry.id,
        "patient_id": entry.patient_id,
        "patient_name": entry.patient.name,
        "phone": entry.patient.phone,
        "status": entry.status.value,
        "created_at": entry.created_at.strftime("%H:%M"),
    }
