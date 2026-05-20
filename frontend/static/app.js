const page = document.body.dataset.page;
const patientId = document.body.dataset.patientId;
const today = new Date().toISOString().slice(0, 10);
let selectedPatient = null;

const $ = (selector) => document.querySelector(selector);

function toast(message) {
  const box = $("#toast");
  box.textContent = message;
  box.style.display = "block";
  clearTimeout(box.timer);
  box.timer = setTimeout(() => {
    box.style.display = "none";
  }, 2400);
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    if (response.status === 401) window.location.href = "/login";
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "حدث خطأ غير متوقع");
  }
  return response.json();
}

function formData(form, extra = {}) {
  const data = new FormData(form);
  Object.entries(extra).forEach(([key, value]) => data.set(key, value));
  return data;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

function money(value) {
  return Number(value || 0).toLocaleString("ar-SA", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function setToday(selector) {
  const input = $(selector);
  if (input) input.value = today;
}

function appointmentStatus(status) {
  return {
    scheduled: "محجوز",
    completed: "تم",
    cancelled: "ملغي",
  }[status] || status;
}

function wireAuth() {
  const loginForm = $("#loginForm");
  const registerForm = $("#registerForm");
  const logoutBtn = $("#logoutBtn");
  const settingsBtn = $("#settingsBtn");
  const settingsPanel = $("#settingsPanel");

  if (settingsBtn && settingsPanel) {
    settingsBtn.addEventListener("click", () => {
      settingsPanel.classList.toggle("open");
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".settings-menu")) {
        settingsPanel.classList.remove("open");
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await request("/api/auth/login", { method: "POST", body: new FormData(event.target) });
        window.location.href = "/patients";
      } catch (error) {
        toast(error.message);
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await request("/api/doctors", { method: "POST", body: new FormData(event.target) });
        await request("/api/auth/login", { method: "POST", body: new FormData(event.target) });
        window.location.href = "/patients";
      } catch (error) {
        toast(error.message);
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await request("/api/auth/logout", { method: "POST" });
      window.location.href = "/login";
    });
  }
}

function setSelectedPatient(patient) {
  selectedPatient = patient;
  const deleteButton = $("#deletePatientBtn");
  const label = $("#selectedPatientText");
  if (!deleteButton || !label) return;
  deleteButton.disabled = !patient;
  label.textContent = patient ? `المحدد: ${patient.name}` : "لم يتم تحديد مريض";
}

async function loadPatients(query = "") {
  const params = new URLSearchParams({ q: query });
  const rows = await request(`/api/patients?${params.toString()}`);
  const table = $("#patientsTable");
  table.innerHTML = rows.map((patient) => `
    <tr class="${selectedPatient?.id === patient.id ? "selected-row" : ""}" data-patient-id="${patient.id}" data-patient-name="${esc(patient.name)}">
      <td class="select-cell">
        <input class="patient-select" type="radio" name="selected_patient" value="${patient.id}" ${selectedPatient?.id === patient.id ? "checked" : ""} aria-label="تحديد ${esc(patient.name)}">
      </td>
      <td><a class="patient-link" href="/patients/${patient.id}">${esc(patient.name)}</a></td>
      <td>${esc(patient.phone)}</td>
      <td>
        <span class="badge">متبقي ${money(patient.total_remaining)}</span>
        <div class="meta">تكلفة ${money(patient.total_cost)} | مدفوع ${money(patient.total_paid)}</div>
      </td>
      <td>${patient.last_visit ? esc(patient.last_visit) : '<span class="meta">لا توجد زيارة</span>'}</td>
      <td>${patient.next_appointment ? esc(patient.next_appointment) : '<span class="meta">لا يوجد موعد</span>'}</td>
      <td><a class="secondary-link" href="/patients/${patient.id}">فتح الملف</a></td>
    </tr>
  `).join("") || `
    <tr>
      <td colspan="7" class="empty">لا توجد نتائج.</td>
    </tr>
  `;

  if (selectedPatient && !rows.some((patient) => patient.id === selectedPatient.id)) {
    setSelectedPatient(null);
  }
}

function wirePatientsPage() {
  const search = $("#patientsSearch");
  const table = $("#patientsTable");
  const deleteButton = $("#deletePatientBtn");

  search.addEventListener("input", () => loadPatients(search.value));
  table.addEventListener("change", (event) => {
    const input = event.target.closest(".patient-select");
    if (!input) return;
    const row = input.closest("[data-patient-id]");
    setSelectedPatient({
      id: Number(row.dataset.patientId),
      name: row.dataset.patientName,
    });
    loadPatients(search.value);
  });

  deleteButton.addEventListener("click", async () => {
    if (!selectedPatient) return;
    const confirmed = window.confirm(`هل تريد حذف المريض "${selectedPatient.name}"؟ سيتم حذف زياراته ومواعيده أيضًا.`);
    if (!confirmed) return;
    try {
      await request(`/api/patients/${selectedPatient.id}`, { method: "DELETE" });
      toast("تم حذف المريض");
      setSelectedPatient(null);
      await loadPatients(search.value);
    } catch (error) {
      toast(error.message);
    }
  });

  loadPatients().catch((error) => toast(error.message));
}

async function createOptionalAppointment(patientIdValue, form) {
  const dateValue = form.appointment_date.value;
  const timeValue = form.appointment_time.value;
  if (!dateValue && !timeValue && !form.reason.value) return;
  if (!dateValue || !timeValue) {
    throw new Error("لإضافة موعد، أدخل التاريخ والوقت معًا");
  }
  const data = new FormData();
  data.set("patient_id", patientIdValue);
  data.set("appointment_date", dateValue);
  data.set("appointment_time", timeValue);
  data.set("reason", form.reason.value);
  await request("/api/appointments", { method: "POST", body: data });
}

async function createOptionalVisit(patientIdValue, form) {
  const hasVisit = form.visit_date.value || form.diagnosis.value || form.cost.value || form.paid.value;
  if (!hasVisit) return;
  const data = new FormData();
  data.set("patient_id", patientIdValue);
  data.set("visit_date", form.visit_date.value || today);
  data.set("diagnosis", form.diagnosis.value);
  data.set("cost", form.cost.value || 0);
  data.set("paid", form.paid.value || 0);
  await request("/api/visits", { method: "POST", body: data });
}

function wireNewPatientPage() {
  $("#createPatientForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    try {
      const patient = await request("/api/patients", { method: "POST", body: formData(form) });
      await createOptionalAppointment(patient.id, form);
      await createOptionalVisit(patient.id, form);
      toast("تم حفظ المريض");
      window.location.href = `/patients/${patient.id}`;
    } catch (error) {
      toast(error.message);
    }
  });
}

async function loadPatient() {
  const patient = await request(`/api/patients/${patientId}`);
  $("#patientName").textContent = patient.name;
  $("#patientMeta").textContent = `${patient.phone} | العمر: ${patient.age || "غير محدد"}`;
  $("#patientNotes").textContent = patient.notes || "لا توجد ملاحظات.";
  $("#patientTotalCost").textContent = money(patient.total_cost);
  $("#patientTotalPaid").textContent = money(patient.total_paid);
  $("#patientTotalRemaining").textContent = money(patient.total_remaining);

  $("#patientAppointments").innerHTML = patient.appointments.map((appointment) => `
    <div class="item">
      <div class="item-title">
        <span>${esc(appointment.date)} - ${esc(appointment.time)}</span>
        <span>${appointmentStatus(appointment.status)}</span>
      </div>
      <div class="meta">${appointment.reason ? esc(appointment.reason) : "بدون سبب محدد"}</div>
    </div>
  `).join("") || `<div class="empty">لا توجد مواعيد.</div>`;

  $("#patientVisits").innerHTML = patient.visits.map((visit) => `
    <div class="item">
      <div class="item-title">
        <span>${esc(visit.date)}</span>
        <span>متبقي ${money(visit.remaining)}</span>
      </div>
      <div class="meta">تكلفة ${money(visit.cost)} | مدفوع ${money(visit.paid)}</div>
      ${visit.diagnosis ? `<div class="meta">${esc(visit.diagnosis)}</div>` : ""}
    </div>
  `).join("") || `<div class="empty">لا توجد زيارات.</div>`;
}

function wirePatientPage() {
  setToday('#patientAppointmentForm [name="appointment_date"]');
  setToday('#patientVisitForm [name="visit_date"]');

  $("#patientAppointmentForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await request("/api/appointments", {
        method: "POST",
        body: formData(event.target, { patient_id: patientId }),
      });
      event.target.reason.value = "";
      toast("تم حفظ الموعد");
      await loadPatient();
    } catch (error) {
      toast(error.message);
    }
  });

  $("#patientVisitForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await request("/api/visits", {
        method: "POST",
        body: formData(event.target, { patient_id: patientId }),
      });
      event.target.diagnosis.value = "";
      event.target.cost.value = "";
      event.target.paid.value = "";
      toast("تم حفظ الزيارة");
      await loadPatient();
    } catch (error) {
      toast(error.message);
    }
  });

  loadPatient().catch((error) => toast(error.message));
}

wireAuth();
if (page === "patients") wirePatientsPage();
if (page === "new-patient") wireNewPatientPage();
if (page === "patient") wirePatientPage();
