from sqlalchemy import inspect, text

from .database import engine


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
