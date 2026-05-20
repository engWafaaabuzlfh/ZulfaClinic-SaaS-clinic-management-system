from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .core.database import Base, engine
from .core.migrations import ensure_schema
from .modules.appointments.routers import router as appointments_router
from .modules.auth.routers import router as auth_router
from .modules.finance.routers import router as finance_router
from .modules.pages.routers import router as pages_router
from .modules.patients_create.routers import router as patients_create_router
from .modules.patients_get.routers import router as patients_get_router
from .modules.queue.routers import router as queue_router
from .modules.visits.routers import router as visits_router


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Zulfa Clinic")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema()


app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(patients_get_router)
app.include_router(patients_create_router)
app.include_router(appointments_router)
app.include_router(queue_router)
app.include_router(visits_router)
app.include_router(finance_router)
