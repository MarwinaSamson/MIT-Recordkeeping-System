const STEPS = [
  { label: "Personal Details", page: "/personalDetails/" },
  {
    label: "Educational Background",
    page: "/educationalBackground/",
  },
  { label: "Working Student", page: "/workingStudent/" },
  { label: "Documents Upload", page: "/documents/" },
  { label: "Privacy Notice", page: "/privacyNotice/" },
  { label: "Review", page: "/review/" },
];
const CURRENT_STEP = 1;

function renderProgress() {
  const bar = document.getElementById("progressBar");
  bar.innerHTML = STEPS.map((step, i) => {
    const num = i + 1;
    const isCompleted = num < CURRENT_STEP;
    const isCurrent = num === CURRENT_STEP;
    let circleClass = "bg-gray-300 text-white";
    if (isCompleted) circleClass = "bg-green-500 text-white";
    if (isCurrent) circleClass = "bg-brand text-white shadow-lg scale-110";
    const checkmark = isCompleted ? "✓" : num;
    const labelClass = isCurrent ? "text-brand font-bold" : "text-gray-400";
    const connector =
      i < STEPS.length - 1
        ? `<div class="flex-1 h-1 mx-2 rounded ${
            num < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"
          }"></div>`
        : "";
    return `
    <div class="flex items-center ${i < STEPS.length - 1 ? "flex-1" : ""}">
      <div class="flex flex-col items-center">
        <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${circleClass}">${checkmark}</div>
        <span class="text-xs mt-2 text-center hidden sm:block max-w-[80px] ${labelClass}">${
          step.label
        }</span>
      </div>
      ${connector}
    </div>`;
  }).join("");
}
renderProgress();

// ===== LOAD SAVED DATA =====
const form = document.getElementById("personalForm");
const saved = JSON.parse(localStorage.getItem("personalDetails") || "{}");
const fields = [
  "first_name",
  "middle_name",
  "last_name",
  "dob",
  "age",
  "gender",
  "civil_status",
  "place_of_birth",
  "religion",
  "religion_other",
  "ethnicity",
  "ethnicity_other",
  "nationality",
  "nationality_other",
  "disability",
  "disability_other",
  "permanent_address",
  "current_address",
  "contact_number",
  "email",
  "name_of_parent",
  "relationship",
  "parent_income",
  "name_of_spouse",
  "spouse_contact_number",
  "spouse_income",
];

fields.forEach((f) => {
  if (saved[f] && form.elements[f]) {
    form.elements[f].value = saved[f];
  }
});

// ===== DATE OF BIRTH - LIMIT TO PAST DATES ONLY =====
const dobInput = document.getElementById("dob");
const ageInput = document.getElementById("age");

if (dobInput) {
  // Set max date to today to prevent future dates
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  const todayFormatted = `${yyyy}-${mm}-${dd}`;

  dobInput.setAttribute("max", todayFormatted);

  // Calculate age when DOB changes
  dobInput.addEventListener("change", function () {
    if (!this.value) {
      ageInput.value = "";
      return;
    }

    const birthDate = new Date(this.value);
    const today = new Date();

    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();

    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }

    ageInput.value = age >= 0 ? age : "";
  });
}

// ===== CONTACT NUMBER - NUMBERS ONLY, MAX 11 DIGITS =====
const contactInput = document.getElementsByName("contact_number")[0];
if (contactInput) {
  contactInput.addEventListener("input", function (e) {
    // Remove any non-digit characters
    this.value = this.value.replace(/\D/g, "");

    // Limit to 11 digits
    if (this.value.length > 11) {
      this.value = this.value.slice(0, 11);
    }
  });
}

// ===== OTHER FIELDS TOGGLE =====
document.querySelectorAll("select[data-other-target]").forEach((select) => {
  const target = document.getElementById(select.dataset.otherTarget);

  function toggleField() {
    if (select.value === "Other") {
      target.classList.remove("hidden");
      target.required = true;
    } else {
      target.classList.add("hidden");
      target.required = false;
      target.value = "";
    }
  }

  select.addEventListener("change", toggleField);
  toggleField(); // run on load (for saved values)
});

// ===== VALIDATION & SUBMIT =====
form.addEventListener("submit", function (e) {
  e.preventDefault();

  // Clear errors
  document
    .querySelectorAll("[data-error]")
    .forEach((el) => el.classList.add("hidden"));

  const data = {};
  fields.forEach((f) => {
    data[f] = form.elements[f]?.value?.trim?.() ?? "";
  });

  const required = [
    "first_name",
    "last_name",
    "dob",
    "gender",
    "civil_status",
    "contact_number",
    "email",
    "place_of_birth",
    "religion",
    "ethnicity",
    "nationality",
    "disability",
    "permanent_address",
    "name_of_parent",
    "relationship",
    "parent_income",
  ];

  let valid = true;
  let firstInvalidField = null;

  function setInvalid(field, msg) {
    if (!firstInvalidField) firstInvalidField = field;
    showError(field, msg);
    valid = false;
  }

  required.forEach((f) => {
    if (!data[f]) {
      setInvalid(f, "This field is required");
    }
  });

  // 'Other' specify fields are required only when the user selects "Other"
  if (data.religion === "Other" && !data.religion_other) {
    setInvalid("religion_other", "Please specify your religion");
  }
  if (data.ethnicity === "Other" && !data.ethnicity_other) {
    setInvalid("ethnicity_other", "Please specify your ethnicity");
  }
  if (data.nationality === "Other" && !data.nationality_other) {
    setInvalid("nationality_other", "Please specify your nationality");
  }
  if (data.disability === "Other" && !data.disability_other) {
    setInvalid("disability_other", "Please specify your disability");
  }

  // Date of birth cannot be in the future
  if (data.dob) {
    const selected = new Date(data.dob);
    const todayCheck = new Date();
    // Compare only date portion (ignore time)
    if (selected.setHours(0, 0, 0, 0) > todayCheck.setHours(0, 0, 0, 0)) {
      setInvalid("dob", "Date of birth cannot be in the future");
    }
  }

  // Email format
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    setInvalid("email", "Invalid email format");
  }

  // Contact number must be exactly 11 digits (no letters)
  if (data.contact_number && !/^\d{11}$/.test(data.contact_number)) {
    setInvalid(
      "contact_number",
      "Contact number must be 11 digits (numbers only)",
    );
  }

  if (!valid) {
    if (firstInvalidField && form.elements[firstInvalidField]) {
      form.elements[firstInvalidField].focus();
    }
    return;
  }

  // Save data to localStorage
  localStorage.setItem("personalDetails", JSON.stringify(data));

  // Submit the form to backend
  form.submit();
});

function showError(field, msg) {
  const el = document.querySelector(`[data-error="${field}"]`);
  if (el) {
    el.textContent = msg;
    el.classList.remove("hidden");
  } else {
    console.error(`Missing <p data-error="${field}"></p> in your HTML.`);
  }
}
