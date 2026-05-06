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

// ===== SAVE MIT CURRICULUM TO LOCALSTORAGE =====
const mitSelect = document.getElementById("mitCurriculum");

// Restore saved value on page load
const savedDocs = JSON.parse(localStorage.getItem("documents") || "{}");
if (savedDocs.mitCurriculum) {
    mitSelect.value = savedDocs.mitCurriculum;
}

// Save on change
mitSelect.addEventListener("change", function () {
    const docs = JSON.parse(localStorage.getItem("documents") || "{}");
    docs.mitCurriculum = this.value;
    localStorage.setItem("documents", JSON.stringify(docs));
});

document.getElementById("documentsForm").addEventListener("submit", function (e) {
    e.preventDefault();
    const docs = JSON.parse(localStorage.getItem("documents") || "{}");
    docs.mitCurriculum = mitSelect.value || "";
    localStorage.setItem("documents", JSON.stringify(docs));
    this.submit();
});