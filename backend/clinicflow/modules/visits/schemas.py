from decimal import Decimal

from ...core.models import Visit


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
