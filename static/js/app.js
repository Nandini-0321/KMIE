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
   5. FORM SUBMIT HANDLERS — PROGRESSIVE ONBOARDING
   ============================================================ */

function attachEnquiryForm() {
  const form = document.getElementById("enquiryForm");
  const btn = document.getElementById("submitEnquiryBtn");
  if (!form || !btn) return;

  form.addEventListener("submit", async function (e) {
    if (!validateEnquiryForm()) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    const originalBtnText = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add("loading");
    btn.innerHTML = '<span class="spinner"></span> Submitting Enquiry…';

    const dupAlert = document.getElementById("duplicateAlert");
    if (dupAlert) dupAlert.style.display = "none";

    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json",
        },
      });

      const data = await response.json();

      if (response.ok && data.success && data.lead) {
        const lead = data.lead;
        document.getElementById("stage2-lead-id").textContent = "#" + lead.id;
        document.getElementById("stage2-student-name").textContent = lead.student_name;
        document.getElementById("stage2-student-phone").textContent = lead.phone;
        document.getElementById("stage2-student-class").textContent = "Class " + lead.class_level + " • " + lead.exam_goal;
        document.getElementById("stage2-student-course").textContent = lead.interested_course;

        const leadIdInput = document.getElementById("lead_id");
        if (leadIdInput) leadIdInput.value = lead.id;
        const stage3Name = document.getElementById("stage3-student-name");
        if (stage3Name) stage3Name.textContent = lead.student_name;

        journeyController.goToStage(2);
      } else if (data.duplicate && data.lead) {
        if (dupAlert) {
          dupAlert.style.display = "flex";
          document.getElementById("duplicateAlertMessage").textContent = data.message;
          const contBtn = document.getElementById("duplicateContinueBtn");
          if (contBtn) {
            contBtn.onclick = function () {
              const lead = data.lead;
              document.getElementById("stage2-lead-id").textContent = "#" + lead.id;
              document.getElementById("stage2-student-name").textContent = lead.student_name;
              document.getElementById("stage2-student-phone").textContent = lead.phone;
              document.getElementById("stage2-student-class").textContent = "Class " + lead.class_level + " • " + lead.exam_goal;
              document.getElementById("stage2-student-course").textContent = lead.interested_course;

              const leadIdInput = document.getElementById("lead_id");
              if (leadIdInput) leadIdInput.value = lead.id;
              const stage3Name = document.getElementById("stage3-student-name");
              if (stage3Name) stage3Name.textContent = lead.student_name;

              journeyController.goToStage(2);
            };
          }
        }
      } else if (data.errors) {
        for (const [field, msg] of Object.entries(data.errors)) {
          showFieldError(field, msg);
        }
      } else {
        alert(data.message || "An error occurred while submitting enquiry.");
      }
    } catch (err) {
      console.warn("AJAX enquiry fallback to standard submit:", err);
      form.submit();
      return;
    } finally {
      btn.disabled = false;
      btn.classList.remove("loading");
      btn.innerHTML = originalBtnText;
    }
  });
}

function attachBookingForm() {
  const form = document.getElementById("bookingForm");
  const btn = document.getElementById("submitBookingBtn");
  if (!form || !btn) return;

  form.addEventListener("submit", async function (e) {
    if (!validateBookingForm()) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    const originalBtnText = btn.innerHTML;
    btn.disabled = true;
    btn.classList.add("loading");
    btn.innerHTML = '<span class="spinner"></span> Confirming Demo Booking…';

    try {
      const formData = new FormData(form);
      const response = await fetch(form.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json",
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        const booking = data.booking || {};
        const studentName = booking.student_name || document.getElementById("stage2-student-name")?.textContent || "";
        const demoDate = booking.demo_date || document.getElementById("demo_date")?.value || "";
        const slotTime = booking.slot_time || document.getElementById("slot_time")?.value || "";

        let slotDisplay = slotTime;
        if (slotTime === "13:00") slotDisplay = "1:00 PM (IST)";
        else if (slotTime === "15:00") slotDisplay = "3:00 PM (IST)";
        else if (slotTime === "17:00") slotDisplay = "5:00 PM (IST)";
        else if (slotTime === "19:00") slotDisplay = "7:00 PM (IST)";

        document.getElementById("conf-student-name").textContent = studentName;
        document.getElementById("conf-demo-date").textContent = demoDate;
        document.getElementById("conf-slot-time").textContent = slotDisplay;
        document.getElementById("conf-status").textContent = booking.booking_status || "Booked";

        journeyController.goToStage(4);
      } else if (data.errors) {
        for (const [field, msg] of Object.entries(data.errors)) {
          showFieldError(field, msg);
        }
      } else {
        alert(data.message || "Failed to schedule demo.");
      }
    } catch (err) {
      console.warn("AJAX booking fallback to standard submit:", err);
      form.submit();
      return;
    } finally {
      btn.disabled = false;
      btn.classList.remove("loading");
      btn.innerHTML = originalBtnText;
    }
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
   8b. GUIDED JOURNEY CONTROLLER
   ============================================================ */

const journeyController = {
  currentStage: 1,

  goToStage: function (stageNumber) {
    this.currentStage = stageNumber;

    // 1. Update Stepper Nav
    for (let i = 1; i <= 4; i++) {
      const stepEl = document.getElementById("step-nav-" + i);
      if (!stepEl) continue;

      stepEl.classList.remove("stepper-step--active", "stepper-step--completed");

      if (i < stageNumber) {
        stepEl.classList.add("stepper-step--completed");
      } else if (i === stageNumber) {
        stepEl.classList.add("stepper-step--active");
      }
    }

    // 2. Update Stepper Lines
    const line12 = document.getElementById("line-1-2");
    const line23 = document.getElementById("line-2-3");
    const line34 = document.getElementById("line-3-4");

    if (line12) line12.classList.toggle("stepper-line--completed", stageNumber > 1);
    if (line23) line23.classList.toggle("stepper-line--completed", stageNumber > 2);
    if (line34) line34.classList.toggle("stepper-line--completed", stageNumber > 3);

    // 3. Show only current stage card
    for (let i = 1; i <= 4; i++) {
      const stageEl = document.getElementById("stage-" + i);
      if (!stageEl) continue;
      if (i === stageNumber) {
        stageEl.style.display = "block";
        stageEl.classList.add("journey-stage--active");
      } else {
        stageEl.style.display = "none";
        stageEl.classList.remove("journey-stage--active");
      }
    }

    // 4. Smooth scroll to top of student journey container
    const container = document.getElementById("studentJourneyApp");
    if (container) {
      container.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // 5. Save state in sessionStorage
    try {
      sessionStorage.setItem("kmie_stage", stageNumber);
    } catch (e) {}
  },

  selectSlot: function (slotValue) {
    const slotSelect = document.getElementById("slot_time");
    if (slotSelect) {
      slotSelect.value = slotValue;
      clearFieldError("slot_time");
    }

    document.querySelectorAll(".slot-card").forEach(function (card) {
      const isSelected = card.getAttribute("data-slot") === slotValue;
      card.classList.toggle("slot-card--selected", isSelected);
      card.setAttribute("aria-checked", isSelected ? "true" : "false");
    });
  },

  copyMeetingLink: function () {
    const urlText = document.getElementById("meetingUrlText")?.textContent?.trim() || "";
    const btn = document.getElementById("copyMeetingBtn");
    if (!urlText) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(urlText).then(function () {
        if (btn) {
          const orig = btn.innerHTML;
          btn.innerHTML = "✅ Copied!";
          btn.classList.add("btn--primary");
          setTimeout(function () {
            btn.innerHTML = orig;
            btn.classList.remove("btn--primary");
          }, 2000);
        }
      });
    } else {
      alert("Demo Session URL: " + urlText);
    }
  },
};
window.journeyController = journeyController;

// Backward-compat for any legacy slot selectors
window.selectQuickSlot = function (val) {
  journeyController.selectSlot(val);
};

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

  // Initialize Journey Stage
  if (document.getElementById("studentJourneyApp")) {
    const confStudentName = document.getElementById("conf-student-name")?.textContent?.trim();
    const stage2StudentName = document.getElementById("stage2-student-name")?.textContent?.trim();

    if (confStudentName && confStudentName !== "") {
      journeyController.goToStage(4);
    } else if (stage2StudentName && stage2StudentName !== "") {
      journeyController.goToStage(2);
    } else {
      journeyController.goToStage(1);
    }
  }
});

