// ===== PROGRESS BAR =====
const STEPS = [
  { label: "Personal Details" },
  { label: "Educational Background" },
  { label: "Working Student" },
  { label: "Documents Upload" },
  { label: "Privacy Notice" },
  { label: "Review" },
];
const CURRENT_STEP = 3;
function renderProgress() {
  const bar = document.getElementById("progressBar");
  bar.innerHTML = STEPS.map((s, i) => {
    const n = i + 1;
    const done = n < CURRENT_STEP;
    const cur = n === CURRENT_STEP;
    let cc = "bg-gray-300 text-white";
    if (done) cc = "bg-green-500 text-white";
    if (cur) cc = "bg-brand text-white shadow-lg scale-110";
    const lc = cur ? "text-brand font-bold" : "text-gray-400";
    const conn =
      i < STEPS.length - 1
        ? `<div class="flex-1 h-1 mx-2 rounded ${
            n < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"
          }"></div>`
        : "";
    return `<div class="flex items-center ${
      i < STEPS.length - 1 ? "flex-1" : ""
    }"><div class="flex flex-col items-center"><div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${cc}">${
      done ? "✓" : n
    }</div><span class="text-xs mt-2 text-center hidden sm:block max-w-[80px] ${lc}">${
      s.label
    }</span></div>${conn}</div>`;
  }).join("");
}
renderProgress();

// ===== TOGGLE EMPLOYMENT FIELDS =====
const checkbox = document.getElementById("isEmployed");
const notEmployedCheckbox = document.getElementById("notEmployed");
const fieldsDiv = document.getElementById("employmentFields");
const saved = JSON.parse(localStorage.getItem("workingStudent") || "{}");

function setEmploymentFieldsVisibility() {
  const employed = checkbox.checked;
  fieldsDiv.classList.toggle("hidden", !employed);
  if (employed) {
    notEmployedCheckbox.checked = false;
  }
}

function setNotEmployedState() {
  if (notEmployedCheckbox.checked) {
    checkbox.checked = false;
    fieldsDiv.classList.add("hidden");
  }
}

// Load saved data
if (saved.isEmployed) {
  checkbox.checked = true;
  fieldsDiv.classList.remove("hidden");
  notEmployedCheckbox.checked = false;
  [
    "position",
    "monthlyIncome",
    "employmentStatus",
    "employmentStatusOther",
    "employerName",
    "employerAddress",
    "employerContact",
    "employerClassification",
    "employerClassificationOther",
  ].forEach((f) => {
    const field = document.querySelector(`[name="${f}"]`);
    if (saved[f] && field) field.value = saved[f];
  });
} else if (saved.isNotEmployed) {
  notEmployedCheckbox.checked = true;
  checkbox.checked = false;
  fieldsDiv.classList.add("hidden");
}

checkbox.addEventListener("change", function () {
  setEmploymentFieldsVisibility();
});

notEmployedCheckbox.addEventListener("change", function () {
  setNotEmployedState();
});

///others (specify)
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

// ===== VALIDATION =====
document.getElementById("workForm").addEventListener("submit", function (e) {
  e.preventDefault();

  // clear all errors
  document
    .querySelectorAll("[data-error]")
    .forEach((el) => el.classList.add("hidden"));
  const statusError = document.getElementById("employmentStatusError");
  statusError.classList.add("hidden");

  const isEmployed = checkbox.checked;
  const isNotEmployed = notEmployedCheckbox.checked;
  const data = { isEmployed: isEmployed && !isNotEmployed, isNotEmployed };

  if (!isEmployed && !isNotEmployed) {
    statusError.textContent = "Please select either employed or not employed.";
    statusError.classList.remove("hidden");
    return;
  }

  if (isNotEmployed) {
    // Not employed: no additional fields required
    localStorage.setItem("workingStudent", JSON.stringify(data));
    this.submit();
    return;
  }

  if (isEmployed) {
    let valid = true;
    // Required fields (including the new classification)
    const reqFields = [
      "position",
      "monthlyIncome",
      "employmentStatus",
      "employerName",
      "employerAddress",
      "employerClassification",
      "employerContact",
    ];

    // Validate main fields
    reqFields.forEach((f) => {
      let field = this.elements[f];
      // skip if field doesn't exist (just in case)
      if (!field) return;
      let val = field.value.trim();
      data[f] = val;
      if (!val) {
        showError(f, "Required");
        valid = false;
      }
    });

    if (!valid) return;
  } else {
    // if not employed, clear any stored employment data (optional, but good practice)
    // preserve the isEmployed flag only.
  }

  localStorage.setItem("workingStudent", JSON.stringify(data));
  // submit to backend for persistence
  this.submit();
});

function showError(f, m) {
  const el = document.querySelector(`[data-error="${f}"]`);
  if (el) {
    el.textContent = m;
    el.classList.remove("hidden");
  }
}

// additionally ensure that if the main select changes after failed validation we don't keep stale errors, but that's optional.
