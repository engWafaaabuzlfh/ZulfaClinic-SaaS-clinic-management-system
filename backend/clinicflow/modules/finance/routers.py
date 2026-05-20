from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.dependencies import current_doctor
from ...core.models import Doctor

from .crud import list_finance_visits
from .schemas import visit_payload


router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("")
def finance_summary(
    db: Annotated[Session, Depends(get_db)],
    doctor: Annotated[Doctor, Depends(current_doctor)],
    day: Annotated[date | None, Query()] = None,
):
    rows = [visit_payload(visit) for visit in list_finance_visits(db, doctor, day)]
    return {
        "rows": rows,
        "total_cost": sum(row["cost"] for row in rows),
        "total_paid": sum(row["paid"] for row in rows),
        "total_remaining": sum(row["remaining"] for row in rows),
    }
