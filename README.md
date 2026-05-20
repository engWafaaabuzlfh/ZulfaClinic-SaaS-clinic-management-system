# ClinicFlow

نظام عيادات بسيط مبني بـ FastAPI وHTML وCSS وJavaScript مع PostgreSQL.

## التشغيل

1. أنشئ قاعدة PostgreSQL باسم `clinicflow`.
2. انسخ `.env.example` إلى `.env` وعدّل بيانات الاتصال.

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/clinicflow
SESSION_SECRET=change-this-secret
```

3. ثبّت الحزم:

```powershell
.\Scripts\python.exe -m pip install -r requirements.txt
```

4. شغّل السيرفر:

```powershell
.\Scripts\python.exe -m uvicorn src.main:app --reload
```

ثم افتح:

```text
http://127.0.0.1:8000/login
```

## الواجهات

- `/register`: إنشاء حساب طبيب. الطبيب هنا هو مستخدم النظام.
- `/login`: تسجيل دخول الطبيب.
- `/patients`: مرضى الطبيب الحالي فقط.
- `/patients/new`: إنشاء مريض جديد مرتبط تلقائيًا بالطبيب الحالي.
- `/patients/{id}`: ملف المريض، ولا يفتح إلا للطبيب مالك المريض.

كل بيانات المرضى والمواعيد والزيارات والكشف المالي معزولة حسب الطبيب المسجل دخوله.
