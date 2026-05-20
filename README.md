# Zulfa Clinic

Zulfa Clinic is a SaaS clinic management system built with FastAPI, PostgreSQL, server-rendered HTML, CSS, and vanilla JavaScript.

The system is designed around doctor-level isolation: every doctor is a user account, and each doctor can only access their own patients, appointments, visits, queue entries, and financial records.

## SaaS Model

Zulfa Clinic currently follows a lightweight multi-tenant SaaS model where each doctor account acts as an isolated tenant.

- Each doctor signs up and logs in with their own account.
- Each patient belongs to one doctor through `doctor_id`.
- All patient records, appointments, queue entries, visits, and financial records are scoped to the authenticated doctor.
- A doctor cannot view or modify another doctor's data.

This makes the current version a doctor-level SaaS. A future clinic-level SaaS version can introduce a separate `Clinic` or `Organization` tenant model, where one clinic can contain multiple doctors, receptionists, and admins.

## Features

- Doctor registration and login.
- Signed cookie-based sessions.
- Patient management per authenticated doctor.
- Patient profile with notes, visits, appointments, and financial summary.
- Appointment creation and updates.
- Queue tracking: waiting, entered, done.
- Simple financial tracking: consultation cost, paid amount, remaining balance.
- Patient search by name or phone number.
- Patient table actions: add patient and delete selected patient.

## Tech Stack

- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Templates: Jinja2
- Frontend: HTML, CSS, vanilla JavaScript
- Auth: PBKDF2 password hashing and signed HTTP-only cookie sessions

## Project Structure

```text
src/
|-- .env.example
|-- README.md
|-- requirements.txt
|-- backend/
|   |-- main.py
|   `-- clinicflow/
|       |-- __init__.py
|       |-- database.py              # compatibility re-export
|       |-- main.py
|       |-- models.py                # compatibility re-export
|       |-- core/
|       |   |-- __init__.py
|       |   |-- database.py
|       |   |-- dependencies.py
|       |   |-- migrations.py
|       |   |-- models.py
|       |   |-- security.py
|       |   `-- utils.py
|       `-- modules/
|           |-- auth/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- patients_create/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- patients_get/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- appointments/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- queue/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- visits/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           |-- finance/
|           |   |-- crud.py
|           |   |-- routers.py
|           |   `-- schemas.py
|           `-- pages/
|               `-- routers.py
`-- frontend/
    |-- static/
    |   |-- app.js
    |   `-- styles.css
    `-- templates/
        `-- index.html
```

## Components

### Backend

- `src/backend/main.py`
  - ASGI entrypoint that exposes the FastAPI app.

- `src/backend/clinicflow/main.py`
  - Main FastAPI application factory-style wiring.
  - Mounts static frontend assets.
  - Registers all feature routers.
  - Runs startup schema checks.

- `src/backend/clinicflow/core/`
  - Shared backend foundation.
  - `database.py`: SQLAlchemy engine, session, and `Base`.
  - `models.py`: SQLAlchemy database models and enums.
  - `security.py`: password hashing and signed session helpers.
  - `dependencies.py`: FastAPI dependencies for authenticated doctor and ownership checks.
  - `migrations.py`: lightweight startup schema compatibility checks.
  - `utils.py`: shared parsing helpers.

- `src/backend/clinicflow/modules/`
  - Feature modules. Each API area is separated into:
    - `routers.py`: FastAPI endpoints.
    - `crud.py`: database operations and business rules.
    - `schemas.py`: response shaping/serialization helpers.

- `src/backend/clinicflow/modules/auth/`
  - Doctor registration, login, logout, current doctor endpoint.

- `src/backend/clinicflow/modules/patients_create/`
  - Patient creation endpoint and related creation logic.

- `src/backend/clinicflow/modules/patients_get/`
  - Patient listing, details, deletion, ownership-safe retrieval.

- `src/backend/clinicflow/modules/appointments/`
  - Appointment listing, creation, and updates.

- `src/backend/clinicflow/modules/queue/`
  - Daily queue listing, adding patients to queue, status updates.

- `src/backend/clinicflow/modules/visits/`
  - Visit creation and visit financial entry creation.

- `src/backend/clinicflow/modules/finance/`
  - Financial summary endpoint.

- `src/backend/clinicflow/modules/pages/`
  - HTML page routes for login, registration, patients list, patient form, and patient profile.

- `src/backend/clinicflow/database.py`
  - Compatibility re-export for `core.database`.

- `src/backend/clinicflow/models.py`
  - Compatibility re-export for `core.models`.

### Frontend

- `src/frontend/templates/index.html`
  - Main Jinja2 template.
  - Renders all application pages depending on the backend-provided `page` value.

- `src/frontend/static/styles.css`
  - Application styling.
  - Layouts for navbar, auth forms, patient table, toolbars, cards, forms, and responsive views.

- `src/frontend/static/app.js`
  - Frontend behavior.
  - Handles login, registration, logout, patient table selection, patient deletion, patient creation, visits, and appointments.

## Environment

Copy the example file:

```powershell
Copy-Item src\.env.example src\.env
```

Example configuration:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/clinicflow
SESSION_SECRET=replace-with-a-long-random-secret
```

## Installation

Install dependencies inside the existing virtual environment:

```powershell
.\Scripts\python.exe -m pip install -r src\requirements.txt
```

## Database

Create a PostgreSQL database named:

```text
clinicflow
```

The app creates tables automatically on startup with `SQLAlchemy.metadata.create_all`.

For older local databases, the app also checks and adds these fields if missing:

- `doctors.password_hash`
- `patients.doctor_id`

## Running

Run the application from the project root:

```powershell
.\Scripts\python.exe -m uvicorn src.backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/login
```

## Frontend Pages

### `/login`

Doctor login page.

Fields:

- Phone number
- Password

### `/register`

Doctor account creation page.

Fields:

- Doctor name
- Phone number
- Specialty
- Password
- Notes

After registration, the frontend logs the doctor in and redirects to `/patients`.

### `/patients`

Authenticated doctor's patient list.

Includes:

- Search by patient name or phone.
- Add patient action.
- Select patient row.
- Delete selected patient.
- Patient financial summary.
- Last visit date.
- Next scheduled appointment.

### `/patients/new`

Create a new patient for the currently logged-in doctor.

Includes:

- Patient information.
- Optional appointment.
- Optional visit and financial record.

### `/patients/{id}`

Patient profile page.

Includes:

- Patient notes.
- Financial summary.
- Appointment list.
- Visit list.
- Add appointment form.
- Add visit and financial record form.

Only the doctor who owns the patient can open this page.

## API Endpoints

All endpoints under `/api/*`, except doctor registration and login, require an authenticated doctor session.

The API layer is organized by module. Each module owns its `routers.py`, `crud.py`, and `schemas.py` files so endpoints do not live in one large backend file.

### Authentication Module

Folder: `src/backend/clinicflow/modules/auth/`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/doctors` | Register a new doctor account. |
| `POST` | `/api/auth/login` | Log in using phone and password. |
| `POST` | `/api/auth/logout` | Clear the current session cookie. |
| `GET` | `/api/doctors` | Return the currently authenticated doctor. |

### Patient Creation Module

Folder: `src/backend/clinicflow/modules/patients_create/`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/patients` | Create a patient owned by the current doctor. |

### Patient Retrieval Module

Folder: `src/backend/clinicflow/modules/patients_get/`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | List patients owned by the current doctor. Supports `q` search query. |
| `GET` | `/api/patients/{patient_id}` | Get one owned patient with visits, appointments, and financial totals. |
| `DELETE` | `/api/patients/{patient_id}` | Delete one owned patient and related child records. |
| `PUT` | `/api/patients/{patient_id}/doctor` | Re-assert ownership for the current doctor. Kept for internal compatibility. |

### Appointments Module

Folder: `src/backend/clinicflow/modules/appointments/`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/appointments?day=YYYY-MM-DD` | List current doctor's appointments for a specific day. Defaults to today. |
| `POST` | `/api/appointments` | Create an appointment for an owned patient. |
| `PUT` | `/api/appointments/{appointment_id}` | Update an appointment owned by the current doctor. |

### Queue Module

Folder: `src/backend/clinicflow/modules/queue/`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/queue?day=YYYY-MM-DD` | List queue entries for the current doctor on a specific day. Defaults to today. |
| `POST` | `/api/queue` | Add an owned patient to the queue. |
| `PUT` | `/api/queue/{entry_id}` | Update queue status: `waiting`, `entered`, or `done`. |

### Visits Module

Folder: `src/backend/clinicflow/modules/visits/`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/visits` | Create a visit and financial record for an owned patient. |

### Finance Module

Folder: `src/backend/clinicflow/modules/finance/`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/finance` | Return financial rows and totals for the current doctor. Supports optional `day=YYYY-MM-DD`. |

## Data Ownership

Every patient has a `doctor_id`.

Backend ownership checks are enforced before reading or writing:

- Patient profiles
- Appointments
- Visits
- Queue entries
- Financial records

If a doctor tries to access another doctor's patient or related records, the API returns `404` to avoid exposing whether the record exists.

## Notes

- The current authentication layer is intentionally simple and suitable for a local/internal clinic app.
- Set a strong `SESSION_SECRET` in production.
- Use HTTPS in production so session cookies are protected in transit.
- For production deployments, consider adding migrations with Alembic instead of startup schema adjustments.
