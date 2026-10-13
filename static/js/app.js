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
   9. FIND MY DEMO BOOKING FEATURE
   ============================================================ */

/* ============================================================
   9. FIND MY DEMO BOOKING FEATURE
   ============================================================ */

window.switchSearchMethod = function (method) {
  const hiddenType = document.getElementById("find_search_type");
  const inputEl = document.getElementById("find_search_value");
  const labelEl = document.getElementById("findInputLabel");
  const hintEl = document.getElementById("findInputHint");
  const errorEl = document.getElementById("findError");

  // Canonicalize method
  const normMethod = method === "id" ? "reference" : (method === "phone" ? "mobile" : method);

  if (hiddenType) hiddenType.value = normMethod;
  if (errorEl) {
    errorEl.textContent = "";
    errorEl.style.display = "none";
  }

  // Update tabs active state
  document.querySelectorAll(".search-tab").forEach(function (tab) {
    const tMethod = tab.getAttribute("data-method");
    const isActive = tMethod === normMethod || (normMethod === "reference" && tMethod === "id") || (normMethod === "mobile" && tMethod === "phone");
    tab.classList.toggle("search-tab--active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });

  if (!inputEl) return;
  inputEl.classList.remove("is-invalid");

  if (normMethod === "mobile" || normMethod === "phone") {
    inputEl.type = "tel";
    inputEl.placeholder = "Enter your registered mobile number";
    if (labelEl) labelEl.innerHTML = 'Mobile Number <span class="required">*</span>';
    if (hintEl) hintEl.textContent = "Enter your 10-digit Indian mobile number (+91 or leading 0 supported).";
  } else if (normMethod === "email") {
    inputEl.type = "email";
    inputEl.placeholder = "Enter your registered email address";
    if (labelEl) labelEl.innerHTML = 'Email Address <span class="required">*</span>';
    if (hintEl) hintEl.textContent = "The email address you provided during student enquiry registration.";
  } else {
    // default: reference
    inputEl.type = "text";
    inputEl.placeholder = "Enter your enquiry or booking reference";
    if (labelEl) labelEl.innerHTML = 'Enquiry / Booking Reference <span class="required">*</span>';
    if (hintEl) hintEl.textContent = "Use your registered Enquiry Reference ID (e.g. 1) or Booking Reference.";
  }
  inputEl.focus();
};

window.clearFindBooking = function () {
  const inputEl = document.getElementById("find_search_value");
  const errorEl = document.getElementById("findError");
  const resultArea = document.getElementById("findResultArea");

  if (inputEl) {
    inputEl.value = "";
    inputEl.classList.remove("is-invalid");
    inputEl.focus();
  }
  if (errorEl) {
    errorEl.textContent = "";
    errorEl.style.display = "none";
  }
  if (resultArea) {
    resultArea.innerHTML = "";
    resultArea.style.display = "none";
  }
};

window.findBookingHandler = function (event) {
  if (event) event.preventDefault();

  const type = document.getElementById("find_search_type")?.value || "reference";
  const inputEl = document.getElementById("find_search_value");
  const val = (inputEl?.value || "").trim();
  const errorEl = document.getElementById("findError");
  const resultArea = document.getElementById("findResultArea");
  const submitBtn = document.getElementById("findBookingSubmitBtn");

  if (errorEl) {
    errorEl.textContent = "";
    errorEl.style.display = "none";
  }
  if (inputEl) inputEl.classList.remove("is-invalid");

  if (!val) {
    if (errorEl) {
      errorEl.textContent = "Please enter your details to search.";
      errorEl.style.display = "block";
    }
    if (inputEl) inputEl.classList.add("is-invalid");
    return false;
  }

  // Client-side quick check
  if (type === "mobile" || type === "phone") {
    const cleaned = val.replace(/[\s\-\.\(\)]/g, "");
    if (cleaned.length < 10) {
      if (errorEl) {
        errorEl.textContent = "Please enter a valid 10-digit mobile number.";
        errorEl.style.display = "block";
      }
      if (inputEl) inputEl.classList.add("is-invalid");
      return false;
    }
  } else if (type === "email") {
    if (!val.includes("@") || !val.includes(".")) {
      if (errorEl) {
        errorEl.textContent = "Please enter a valid email address.";
        errorEl.style.display = "block";
      }
      if (inputEl) inputEl.classList.add("is-invalid");
      return false;
    }
  }

  // Button loading state
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Searching...';
  }

  const url = "/booking/find?search_type=" + encodeURIComponent(type) + "&search_value=" + encodeURIComponent(val);

  fetch(url, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "Accept": "application/json",
    },
  })
    .then(function (resp) {
      return resp.json().then(function (data) {
        return { status: resp.status, data: data };
      });
    })
    .then(function (res) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🔍</span> Find My Details';
      }

      if (!resultArea) return;
      resultArea.style.display = "block";

      // State E: Not found
      if (res.data.not_found || res.data.state === "not_found") {
        resultArea.innerHTML = `
          <div class="find-alert find-alert--warning" role="alert">
            <span class="find-alert-icon">⚠️</span>
            <div class="find-alert-body">
              <strong>${escapeHtml(res.data.title || "We couldn't find your record.")}</strong>
              <p>${escapeHtml(res.data.message || "Check the details you entered and try again, or contact KMIE administration for assistance.")}</p>
              <div style="margin-top: 10px;">
                <button type="button" class="btn btn--xs btn--outline" onclick="clearFindBooking()">🔍 Search Again</button>
              </div>
            </div>
          </div>
        `;
        return;
      }

      if (!res.data.success) {
        const errMsg = res.data.error || "An error occurred while retrieving your details.";
        if (errorEl) {
          errorEl.textContent = errMsg;
          errorEl.style.display = "block";
        }
        if (inputEl) inputEl.classList.add("is-invalid");
        resultArea.style.display = "none";
        return;
      }

      // Multiple records state
      if (res.data.state === "multiple_records" && Array.isArray(res.data.matches)) {
        let matchesListHtml = res.data.matches.map(function(item) {
          const bookingInfo = item.has_booking ? `${item.demo_date} at ${item.slot_time_display} (${item.booking_status})` : 'Enquiry Registered (No Demo Booked)';
          return `
            <div class="find-match-row">
              <div class="find-match-info">
                <strong>${escapeHtml(item.student_name)}</strong>
                <span class="find-match-sub">Lead #${item.lead_id} • Class ${item.class_level || '11/12'} • ${escapeHtml(item.exam_goal || '')}</span>
                <span class="find-match-status">${escapeHtml(bookingInfo)}</span>
              </div>
              <button type="button" class="btn btn--xs btn--primary" onclick="searchBySpecificReference('${item.lead_id}')">
                Select This Record →
              </button>
            </div>
          `;
        }).join("");

        resultArea.innerHTML = `
          <div class="find-result-card">
            <div class="find-result-header">
              <span class="find-badge-info">Multiple Records Found</span>
            </div>
            <p style="font-size: 13px; color: #475569; margin: 0 0 12px 0;">
              ${escapeHtml(res.data.message || "Please select your specific registration below:")}
            </p>
            <div class="find-matches-list">${matchesListHtml}</div>
            <div style="margin-top: 14px;">
              <button type="button" class="btn btn--ghost" onclick="clearFindBooking()">← Search Again</button>
            </div>
          </div>
        `;
        return;
      }

      // Single record rendering
      const d = res.data.data;
      const state = res.data.state || (res.data.has_booking ? "booking_confirmed" : "enquiry_registered");

      // Shared Detail Rows
      const studentClassText = d.class_level ? `Class ${d.class_level} • ${d.exam_goal || ''} — ${d.interested_course || ''}` : (d.interested_course || '—');
      const bookingDateTime = d.demo_date_formatted ? `${d.demo_date_formatted} at ${d.slot_time_display || d.slot_time}` : (d.demo_date ? `${d.demo_date} at ${d.slot_time_display || d.slot_time}` : 'Not scheduled yet');

      let contextualActionHtml = "";

      // STATE A: Enquiry Registered, No Demo Booking
      if (state === "enquiry_registered") {
        contextualActionHtml = `
          <div class="find-context-box find-context-box--info">
            <div class="find-context-header">
              <span class="find-badge-warning">Enquiry Registered</span>
            </div>
            <p class="find-context-msg">Your enquiry is saved. Choose a date and time to schedule your demo.</p>
            <div class="find-actions-row">
              <button type="button" class="btn btn--primary btn--lg" onclick="activateAndBookLead(${d.lead_id}, '${escapeHtml(d.student_name)}')">
                <span class="btn-icon">📅</span> Book My Demo
              </button>
              <button type="button" class="btn btn--ghost" onclick="clearFindBooking()">
                🔍 Search Again
              </button>
            </div>
          </div>
        `;
      }
      // STATE B: Demo Booking Confirmed (Meeting Link Available)
      else if (state === "booking_confirmed") {
        const meetingUrl = d.zoom_link;
        contextualActionHtml = `
          <div class="find-context-box find-context-box--success">
            <div class="find-context-header">
              <span class="find-badge-success">Demo Session Booked</span>
            </div>
            
            <!-- Dedicated Meeting Link Card -->
            <div class="find-meeting-link-card">
              <h4 class="find-meeting-heading">Your Demo Meeting Link</h4>
              <p class="find-meeting-subtitle">Use this link to join your scheduled session at the confirmed date and time.</p>
              
              <div class="find-meeting-box">
                <div class="find-meeting-link-row">
                  <code class="find-meeting-code" id="retrievedMeetingUrl">${escapeHtml(meetingUrl)}</code>
                  <button type="button" class="btn btn--xs btn--outline" onclick="copyRetrievedMeetingLink()">📋 Copy Link</button>
                </div>
              </div>

              <div class="find-actions-row" style="margin-top: 14px;">
                <a href="${escapeHtml(meetingUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn--primary btn--lg" id="joinRetrievedMeetingBtn">
                  <span class="btn-icon">🚀</span> Join Demo Session
                </a>
                <button type="button" class="btn btn--ghost" onclick="clearFindBooking()">
                  🔍 Search Again
                </button>
              </div>
            </div>
          </div>
        `;
      }
      // STATE C: Booking Confirmed but Meeting Link Missing
      else if (state === "booking_no_link") {
        contextualActionHtml = `
          <div class="find-context-box find-context-box--warning">
            <div class="find-context-header">
              <span class="find-badge-success">Demo Session Booked</span>
            </div>
            <div class="find-alert find-alert--warning" style="margin-top: 10px;">
              <span class="find-alert-icon">ℹ️</span>
              <div class="find-alert-body">
                <strong>Meeting Link Notice</strong>
                <p>Your booking is confirmed, but the meeting link is not currently available. Please contact KMIE administration.</p>
              </div>
            </div>
            <div class="find-actions-row" style="margin-top: 14px;">
              <button type="button" class="btn btn--ghost" onclick="clearFindBooking()">
                🔍 Search Again
              </button>
            </div>
          </div>
        `;
      }
      // STATE D: Attended or Not Attended
      else if (state === "booking_attended" || state === "booking_not_attended") {
        const isAttended = state === "booking_attended";
        const statusBadge = isAttended ? '<span class="find-badge-attended">Attended</span>' : '<span class="find-badge-missed">Not Attended</span>';
        const statusMsg = isAttended 
          ? "This session has been marked as Attended. Thank you for participating in the KMIE demo." 
          : "This session was marked as Not Attended. Please contact KMIE administration if you would like to reschedule.";

        contextualActionHtml = `
          <div class="find-context-box">
            <div class="find-context-header">
              ${statusBadge}
            </div>
            <p class="find-context-msg">${escapeHtml(statusMsg)}</p>
            <div class="find-actions-row" style="margin-top: 14px;">
              <button type="button" class="btn btn--ghost" onclick="clearFindBooking()">
                🔍 Search Again
              </button>
            </div>
          </div>
        `;
      }

      // Assemble 3-part layout: Details Grid + Contextual Action Area
      resultArea.innerHTML = `
        <div class="find-result-card">
          <div class="find-result-header">
            <span class="find-record-title">Appointment &amp; Enquiry Details</span>
            <span class="find-header-ref">Ref #${d.lead_id}</span>
          </div>

          <!-- Responsive Two-Column Detail Layout -->
          <div class="find-details-grid">
            <div class="find-item">
              <span class="find-label">Student Name</span>
              <strong class="find-value">${escapeHtml(d.student_name)}</strong>
            </div>
            <div class="find-item">
              <span class="find-label">Enquiry Reference</span>
              <strong class="find-value">Lead #${d.lead_id}</strong>
            </div>
            <div class="find-item">
              <span class="find-label">Masked Mobile</span>
              <strong class="find-value">${escapeHtml(d.phone_masked)}</strong>
            </div>
            <div class="find-item">
              <span class="find-label">Masked Email</span>
              <strong class="find-value">${escapeHtml(d.email_masked)}</strong>
            </div>
            <div class="find-item">
              <span class="find-label">Class &amp; Course</span>
              <strong class="find-value">${escapeHtml(studentClassText)}</strong>
            </div>
            <div class="find-item">
              <span class="find-label">Demo Date &amp; Time</span>
              <strong class="find-value text-teal">${escapeHtml(bookingDateTime)}</strong>
            </div>
          </div>

          <!-- Contextual Action Area -->
          ${contextualActionHtml}
        </div>
      `;

      resultArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
    })
    .catch(function (err) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🔍</span> Find My Details';
      }
      if (resultArea) {
        resultArea.style.display = "block";
        resultArea.innerHTML = `
          <div class="find-alert find-alert--error" role="alert">
            <span class="find-alert-icon">❌</span>
            <div class="find-alert-body">
              <strong>Error Loading Details</strong>
              <p>A network or server error occurred. Please try again.</p>
            </div>
          </div>
        `;
      }
    });

  return false;
};

window.searchBySpecificReference = function (refId) {
  switchSearchMethod("reference");
  const inputEl = document.getElementById("find_search_value");
  if (inputEl) inputEl.value = refId;
  findBookingHandler();
};

window.copyRetrievedMeetingLink = function () {
  const url = document.getElementById("retrievedMeetingUrl")?.textContent?.trim();
  if (!url) return;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(function () {
      alert("✅ Meeting link copied to clipboard!");
    });
  } else {
    alert("Demo Session URL: " + url);
  }
};

window.activateAndBookLead = function (leadId, studentName) {
  const leadInput = document.getElementById("lead_id");
  if (leadInput) leadInput.value = leadId;

  const stage3Student = document.getElementById("stage3-student-name");
  if (stage3Student && studentName) stage3Student.textContent = studentName;

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
  fetch("/booking/activate-lead/" + leadId, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
  }).finally(function () {
    journeyController.goToStage(3);
  });
};

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
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

