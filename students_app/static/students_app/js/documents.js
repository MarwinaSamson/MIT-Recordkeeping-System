// ===== PROGRESS BAR =====
const STEPS = [
  { label: "Personal Details" },
  { label: "Educational Background" },
  { label: "Working Student" },
  { label: "Documents Upload" },
  { label: "Privacy Notice" },
  { label: "Review" },
];
const CURRENT_STEP = 4;

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
        ? `<div class="flex-1 h-1 mx-2 rounded ${n < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"}"></div>`
        : "";
    return `<div class="flex items-center ${i < STEPS.length - 1 ? "flex-1" : ""}"><div class="flex flex-col items-center"><div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${cc}">${done ? "✓" : n}</div><span class="text-xs mt-2 text-center hidden sm:block max-w-[80px] ${lc}">${s.label}</span></div>${conn}</div>`;
  }).join("");
}
renderProgress();

// ===== PREVIEW FUNCTION =====
function setupPreview(fileInput, previewElement) {
  fileInput.addEventListener("change", function () {
    if (this.files && this.files[0]) {
      const file = this.files[0];

      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewElement.innerHTML = `<img src="${e.target.result}" class="w-full h-full object-cover" />`;
        };
        reader.readAsDataURL(file);
      } else if (file.type === "application/pdf") {
        previewElement.innerHTML =
          '<i class="fas fa-file-pdf text-2xl text-red-500"></i>';
      } else {
        previewElement.innerHTML =
          '<i class="fas fa-file text-2xl text-gray-400"></i>';
      }
    } else {
      previewElement.innerHTML = '<i class="fas fa-image text-2xl"></i>';
    }
  });
}

// Setup previews for single file inputs
setupPreview(
  document.querySelector(".deansRec-file"),
  document.querySelector(".deansRec-preview"),
);
setupPreview(
  document.querySelector(".honorable-file"),
  document.querySelector(".honorable-preview"),
);
setupPreview(
  document.querySelector(".gsat-file"),
  document.querySelector(".gsat-preview"),
);
setupPreview(
  document.querySelector(".tor-pdf-file"),
  document.querySelector(".tor-pdf-preview"),
);
setupPreview(
  document.querySelector(".psa-pdf-file"),
  document.querySelector(".psa-pdf-preview"),
);

// ===== TOR Image Section =====
function setupImageSection(
  containerId,
  addBtnId,
  itemClass,
  inputClass,
  previewClass,
  removeBtnClass,
  nameAttr,
) {
  const container = document.getElementById(containerId);
  const addBtn = document.getElementById(addBtnId);

  function createImageItem() {
    const item = document.createElement("div");
    item.className = `${itemClass} flex items-start gap-3 bg-white p-3 rounded-lg border border-gray-200 file-item`;
    item.innerHTML = `
                    <div class="flex-grow">
                        <input type="file" name="${nameAttr}" accept=".jpg,.jpeg,.png"
                            class="${inputClass} w-full rounded-lg border border-gray-300 px-3 py-2 file:mr-4 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-brand/10 file:text-brand hover:file:bg-brand/20 transition" />
                    </div>
                    <div class="${previewClass} flex-shrink-0 w-20 h-20 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center text-gray-400 overflow-hidden">
                        <i class="fas fa-image text-2xl"></i>
                    </div>
                    <button type="button" class="${removeBtnClass} text-red-500 hover:text-red-700 p-1">
                        <i class="fas fa-times"></i>
                    </button>
                `;
    return item;
  }

  addBtn.addEventListener("click", function () {
    const newItem = createImageItem();
    container.appendChild(newItem);

    // Setup preview for new item
    const fileInput = newItem.querySelector(`.${inputClass}`);
    const previewDiv = newItem.querySelector(`.${previewClass}`);
    setupPreview(fileInput, previewDiv);

    // Setup remove button
    const removeBtn = newItem.querySelector(`.${removeBtnClass}`);
    removeBtn.addEventListener("click", function () {
      if (container.children.length > 1) {
        newItem.remove();
      }
    });
  });

  // Setup existing items
  document.querySelectorAll(`.${itemClass}`).forEach((item) => {
    const fileInput = item.querySelector(`.${inputClass}`);
    const previewDiv = item.querySelector(`.${previewClass}`);
    setupPreview(fileInput, previewDiv);

    const removeBtn = item.querySelector(`.${removeBtnClass}`);
    if (removeBtn) {
      removeBtn.addEventListener("click", function () {
        if (container.children.length > 1) {
          item.remove();
        }
      });
    }
  });
}

// Initialize TOR and PSA image sections
setupImageSection(
  "tor-images-container",
  "add-tor-image",
  "tor-image-item",
  "tor-image-input",
  "tor-image-preview",
  "remove-tor-image",
  "torImages[]",
);
setupImageSection(
  "psa-images-container",
  "add-psa-image",
  "psa-image-item",
  "psa-image-input",
  "psa-image-preview",
  "remove-psa-image",
  "psaImages[]",
);

// ===== VALIDATION =====
document
  .getElementById("documentsForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();

    // Clear previous errors
    document
      .querySelectorAll("[data-error]")
      .forEach((el) => el.classList.add("hidden"));

    let valid = true;

    // Validate Dean's Recommendation
    const deansRec = this.elements["deansRec"];
    if (!deansRec.files.length) {
      showError("deansRec", "Dean's Recommendation is required");
      valid = false;
    }

    // Validate TOR (either PDF or at least one image)
    const torPDF = document.getElementById("torPDF");
    const torImages = document.querySelectorAll('input[name="torImages[]"]');
    let torHasPDF = torPDF.files.length > 0;
    let torHasImage = false;
    torImages.forEach((input) => {
      if (input.files.length > 0) torHasImage = true;
    });

    if (!torHasPDF && !torHasImage) {
      showError(
        "tor",
        "Please upload either a PDF file or at least one image of your TOR",
      );
      valid = false;
    }

    // Validate Honorable Dismissal
    const honorableDismissal = this.elements["honorableDismissal"];
    if (!honorableDismissal.files.length) {
      showError("honorableDismissal", "Honorable Dismissal is required");
      valid = false;
    }

    // Validate PSA (either PDF or at least one image)
    const psaPDF = document.getElementById("psaPDF");
    const psaImages = document.querySelectorAll('input[name="psaImages[]"]');
    let psaHasPDF = psaPDF.files.length > 0;
    let psaHasImage = false;
    psaImages.forEach((input) => {
      if (input.files.length > 0) psaHasImage = true;
    });

    if (!psaHasPDF && !psaHasImage) {
      showError(
        "psa",
        "Please upload either a PDF file or at least one image of your PSA",
      );
      valid = false;
    }

    // Validate GSAT
    const gsat = this.elements["gsat"];
    if (!gsat.files.length) {
      showError("gsat", "GSAT is required");
      valid = false;
    }

    if (!valid) return;

    // Count files for storage
    const torImageCount = Array.from(torImages).filter(
      (input) => input.files.length > 0,
    ).length;
    const psaImageCount = Array.from(psaImages).filter(
      (input) => input.files.length > 0,
    ).length;

    // Save document metadata to localStorage for potential use in review
    localStorage.setItem(
      "documents",
      JSON.stringify({
        deansRec: deansRec.files[0]?.name || null,
        tor: torHasPDF ? "PDF file" : `${torImageCount} image(s)`,
        honorableDismissal: honorableDismissal.files[0]?.name || null,
        psa: psaHasPDF ? "PDF file" : `${psaImageCount} image(s)`,
        gsat: gsat.files[0]?.name || null,
        uploaded: true,
      }),
    );

    // Redirect to next step
    window.location.href = "/privacyNotice/";
  });

function showError(fieldName, message) {
  const errorEl = document.querySelector(`[data-error="${fieldName}"]`);
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.remove("hidden");
  }
}
