/**
 * app.js — KMIE Student Enquiry & Demo Booking
 * Vanilla JavaScript: client-side validation, UX enhancements.
 * NO simulated database operations. All real data comes from Flask + SQLite.
 */

"use strict";

/* ============================================================
   1. UTILITY HELPERS
   ============================================================ */

/** Set today's date as min for all date inputs */
function setDateMinToday() {
  const today = new Date().toISOString().split("T")[0];
  document.querySelectorAll('input[type="date"]').forEach((el) => {
    el.min = today;
    if (!el.value) el.value = today;
  });
}

/** Show an inline error on a form field */
function showFieldError(fieldId, message) {
  const errEl = document.getElementById("err-" + fieldId);
  const inputEl = document.getElementById(fieldId);
  if (errEl) errEl.textContent = message;
  if (inputEl) inputEl.classList.add("is-invalid");
}

/** Clear inline error */
function clearFieldError(fieldId) {
  const errEl = document.getElementById("err-" + fieldId);
  const inputEl = document.getElementById(fieldId);
  if (errEl) errEl.textContent = "";
  if (inputEl) inputEl.classList.remove("is-invalid");
}

/** Mark a field as valid */
function markValid(fieldId) {
  const inputEl = document.getElementById(fieldId);
  if (inputEl) {
    inputEl.classList.remove("is-invalid");
    inputEl.classList.add("is-valid");
  }
}

/** Clear all enquiry form errors */
function clearEnquiryErrors() {
  [
    "student_name",
    "phone",
    "email",
    "class_level",
    "student_class",
    "exam_goal",
    "interested_course",
    "course",
  ].forEach(clearFieldError);
  document.querySelectorAll("#enquiryForm .form-control").forEach((el) =>
    el.classList.remove("is-valid", "is-invalid")
  );
}

/** Clear all booking form errors */
function clearBookingErrors() {
  ["lead_id", "demo_date", "slot_time", "demo_time"].forEach(clearFieldError);
}

/* ============================================================
   2. INDIAN PHONE VALIDATION (mirrors Python logic)
   ============================================================ */

function normalizePhone(raw) {
  if (!raw || typeof raw !== "string") return null;
  let cleaned = raw.trim().replace(/[\s\-\.\(\)]/g, "");

  if (cleaned.startsWith("+91")) cleaned = cleaned.slice(3);
  else if (cleaned.startsWith("0091")) cleaned = cleaned.slice(4);
  else if (cleaned.startsWith("91") && cleaned.length === 12) cleaned = cleaned.slice(2);
  else if (cleaned.startsWith("0") && cleaned.length === 11) cleaned = cleaned.slice(1);

  if (/^[6-9]\d{9}$/.test(cleaned)) return cleaned;
  return null;
}

/* ============================================================
   3. ENQUIRY FORM VALIDATION
   ============================================================ */

function validateEnquiryForm() {
  clearEnquiryErrors();
  let valid = true;

  // Student name
  const name = (document.getElementById("student_name")?.value || "").trim();
  if (!name) {
    showFieldError("student_name", "Student name is required.");
    valid = false;
  } else if (name.length < 2) {
    showFieldError("student_name", "Name must be at least 2 characters.");
    valid = false;
  } else {
    markValid("student_name");
  }

  // Phone
  const phone = (document.getElementById("phone")?.value || "").trim();
  if (!phone) {
    showFieldError("phone", "Phone number is required.");
    valid = false;
  } else if (!normalizePhone(phone)) {
    showFieldError(
      "phone",
      "Enter a valid 10-digit Indian mobile number (starting 6–9). +91 accepted."
    );
    valid = false;
  } else {
    markValid("phone");
  }

  // Email
  const email = (document.getElementById("email")?.value || "").trim();
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  if (!email) {
    showFieldError("email", "Email address is required.");
    valid = false;
  } else if (!emailRe.test(email)) {
    showFieldError("email", "Enter a valid email address.");
    valid = false;
  } else {
    markValid("email");
  }

  // Class
  const classEl = document.getElementById("class_level") || document.getElementById("student_class");
  const cls = (classEl?.value || "").trim();
  const classField = classEl?.id || "class_level";
  if (!cls) {
    showFieldError(classField, "Please select a class.");
    valid = false;
  } else {
    markValid(classField);
  }

  // Exam goal
  const eg = (document.getElementById("exam_goal")?.value || "").trim();
  if (!eg) {
    showFieldError("exam_goal", "Please select an exam goal.");
    valid = false;
  } else {
    markValid("exam_goal");
  }

  // Course
  const courseEl = document.getElementById("interested_course") || document.getElementById("course");
  const course = (courseEl?.value || "").trim();
  const courseField = courseEl?.id || "interested_course";
  if (!course) {
    showFieldError(courseField, "Please select an interested course.");
    valid = false;
  } else {
    markValid(courseField);
  }

  return valid;
}

/* ============================================================
   4. BOOKING FORM VALIDATION
   ============================================================ */

function validateBookingForm() {
  clearBookingErrors();
  let valid = true;

  // Lead
  const leadId = (document.getElementById("lead_id")?.value || "").trim();
  if (!leadId) {
    showFieldError("lead_id", "Please select a student lead.");
    valid = false;
  } else {
    markValid("lead_id");
  }

  // Date
  const demoDate = (document.getElementById("demo_date")?.value || "").trim();
  if (!demoDate) {
    showFieldError("demo_date", "Please select a demo date.");
    valid = false;
  } else {
    const today = new Date().toISOString().split("T")[0];
    if (demoDate < today) {
      showFieldError("demo_date", "Demo date must be today or in the future.");
      valid = false;
    } else {
      markValid("demo_date");
    }
  }

  // Time slot
  const slotEl = document.getElementById("slot_time") || document.getElementById("demo_time");
  const slot = (slotEl?.value || "").trim();
  const slotField = slotEl?.id || "slot_time";
  if (!slot) {
    showFieldError(slotField, "Please select a time slot.");
    valid = false;
  } else {
    markValid(slotField);
  }

  return valid;
}

/* ============================================================
   5. FORM SUBMIT HANDLERS — loading states
   ============================================================ */

function attachEnquiryForm() {
  const form = document.getElementById("enquiryForm");
  const btn = document.getElementById("submitEnquiryBtn");
  if (!form || !btn) return;

  form.addEventListener("submit", function (e) {
    if (!validateEnquiryForm()) {
      e.preventDefault();
      return;
    }
    btn.classList.add("loading");
    btn.innerHTML = '<span class="spinner"></span> Submitting…';
  });
}

function attachBookingForm() {
  const form = document.getElementById("bookingForm");
  const btn = document.getElementById("submitBookingBtn");
  if (!form || !btn) return;

  form.addEventListener("submit", function (e) {
    if (!validateBookingForm()) {
      e.preventDefault();
      return;
    }
    btn.classList.add("loading");
    btn.innerHTML = '<span class="spinner"></span> Booking…';
  });
}

/* ============================================================
   6. AUTO-DISMISS FLASH MESSAGES
   ============================================================ */

function autoDismissFlash() {
  const container = document.getElementById("flash-container");
  if (!container) return;
  // Auto-dismiss non-booking-success flashes after 8 seconds
  container.querySelectorAll(".flash:not(.flash--booking_success)").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.5s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 8000);
  });
}

/* ============================================================
   7. REAL-TIME FIELD VALIDATION ON BLUR
   ============================================================ */

function attachLiveValidation() {
  // Phone
  const phoneEl = document.getElementById("phone");
  if (phoneEl) {
    phoneEl.addEventListener("blur", function () {
      const v = this.value.trim();
      if (!v) return;
      if (!normalizePhone(v)) {
        showFieldError("phone", "Invalid Indian mobile number.");
      } else {
        clearFieldError("phone");
        markValid("phone");
      }
    });
  }

  // Email
  const emailEl = document.getElementById("email");
  if (emailEl) {
    emailEl.addEventListener("blur", function () {
      const v = this.value.trim();
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
      if (!v) return;
      if (!re.test(v)) {
        showFieldError("email", "Enter a valid email address.");
      } else {
        clearFieldError("email");
        markValid("email");
      }
    });
  }

  // Date
  const dateEl = document.getElementById("demo_date");
  if (dateEl) {
    dateEl.addEventListener("change", function () {
      const today = new Date().toISOString().split("T")[0];
      if (this.value < today) {
        showFieldError("demo_date", "Demo date must be today or in the future.");
        this.classList.add("is-invalid");
      } else {
        clearFieldError("demo_date");
        this.classList.remove("is-invalid");
      }
    });
  }
}

/* ============================================================
   8. SCROLL TO FLASH & UI CONTROLS
   ============================================================ */
function scrollToFlash() {
  const container = document.getElementById("flash-container");
  if (container && container.children.length > 0) {
    container.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function attachPasswordToggle() {
  const toggleBtn = document.getElementById("togglePasswordBtn");
  const passwordInput = document.getElementById("password");
  if (!toggleBtn || !passwordInput) return;

  toggleBtn.addEventListener("click", function () {
    const isPassword = passwordInput.getAttribute("type") === "password";
    passwordInput.setAttribute("type", isPassword ? "text" : "password");
    toggleBtn.textContent = isPassword ? "🙈" : "👁️";
    toggleBtn.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
  });
}

function attachTopNavToggle() {
  const toggleBtn = document.getElementById("topNavToggle");
  const navMenu = document.getElementById("topNavMenu");
  if (!toggleBtn || !navMenu) return;

  function closeMenu() {
    navMenu.classList.remove("is-open");
    toggleBtn.setAttribute("aria-expanded", "false");
    toggleBtn.focus();
  }

  toggleBtn.addEventListener("click", function () {
    const isOpen = navMenu.classList.toggle("is-open");
    toggleBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  // Support Escape key to close navigation menu and return focus
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && navMenu.classList.contains("is-open")) {
      closeMenu();
    }
  });

  // Close when clicking outside
  document.addEventListener("click", function (e) {
    if (
      navMenu.classList.contains("is-open") &&
      !navMenu.contains(e.target) &&
      !toggleBtn.contains(e.target)
    ) {
      navMenu.classList.remove("is-open");
      toggleBtn.setAttribute("aria-expanded", "false");
    }
  });
}

function attachMobileSidebarToggle() {
  const toggleBtn = document.getElementById("mobileSidebarToggle");
  const sidebar = document.getElementById("adminSidebar");
  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener("click", function () {
    sidebar.classList.toggle("is-open");
    const isOpen = sidebar.classList.contains("is-open");
    toggleBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebar.classList.contains("is-open")) {
      sidebar.classList.remove("is-open");
      toggleBtn.setAttribute("aria-expanded", "false");
      toggleBtn.focus();
    }
  });
}

/* ============================================================
   9. INIT
   ============================================================ */
document.addEventListener("DOMContentLoaded", function () {
  setDateMinToday();
  attachEnquiryForm();
  attachBookingForm();
  attachLiveValidation();
  attachPasswordToggle();
  attachTopNavToggle();
  attachMobileSidebarToggle();
  autoDismissFlash();
  scrollToFlash();
});
