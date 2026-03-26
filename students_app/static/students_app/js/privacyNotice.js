// ===== PROGRESS BAR =====
const STEPS = [
    { label: "Personal Details", page: "/personalDetails/" },
    { label: "Educational Background", page: "/educationalBackground/" },
    { label: "Working Student", page: "/workingStudent/" },
    { label: "Documents Upload", page: "/documents/" },
    { label: "Privacy Notice", page: "/privacyNotice/" },
    { label: "Review", page: "/review/" },
];
const CURRENT_STEP = 5;

function renderProgress() {
    const bar = document.getElementById("progressBar");
    bar.innerHTML = STEPS.map((step, i) => {
        const num = i + 1;
        const isCompleted = num < CURRENT_STEP;
        const isCurrent = num === CURRENT_STEP;
        let circleClass = "bg-gray-300 text-white";
        if (isCompleted) circleClass = "bg-green-500 text-white";
        if (isCurrent)
            circleClass = "bg-brand text-white shadow-lg scale-110";
        const checkmark = isCompleted ? "✓" : num;
        const labelClass = isCurrent
            ? "text-brand font-bold"
            : "text-gray-400";
        const connector =
            i < STEPS.length - 1
                ? `<div class="flex-1 h-1 mx-2 rounded ${num < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"
                }"></div>`
                : "";
        return `<div class="flex items-center ${i < STEPS.length - 1 ? "flex-1" : ""
            }"><div class="flex flex-col items-center"><div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${circleClass}">${checkmark
            }</div><span class="text-xs mt-2 text-center hidden sm:block max-w-[80px] ${labelClass}">${step.label
            }</span></div>${connector}</div>`;
    }).join("");
}
renderProgress();

        // ===== AUTO-FILL NAME =====
        const personal = JSON.parse(
            localStorage.getItem("personalDetails") || "{}"
        );
        const fullName = [
            personal.firstName,
            personal.middleName,
            personal.lastName,
            personal.suffix ? `, ${personal.suffix}` : ""
        ]
            .filter(Boolean)
            .join(" ");

        // Also get course/program if available
        const educational = JSON.parse(localStorage.getItem("educationalBackground") || "{}");

        document.getElementById("sigName").textContent =
            fullName || "Student Full Name";

        // ===== CHECKBOX TOGGLE =====
        const checkbox = document.getElementById("agreeCheckbox");
        const sigSection = document.getElementById("signatureSection");
        const nextBtn = document.getElementById("nextBtn");

        // Load saved state
        if (localStorage.getItem("privacyAgreed") === "false") {
            checkbox.checked = true;
            sigSection.classList.remove("hidden");
            nextBtn.disabled = false;
            nextBtn.classList.remove("opacity-50", "cursor-not-allowed");
        }

        checkbox.addEventListener("change", function () {
            const agreed = this.checked;

            if (agreed) {
                // When checked, show signature section with understanding
                sigSection.classList.remove("hidden");
                nextBtn.disabled = false;
                nextBtn.classList.remove("opacity-50", "cursor-not-allowed");

                // Log the digital signature event (optional - could be saved to localStorage)
                const signatureData = {
                    name: fullName,
                    date: new Date().toISOString(),
                    ipAddress: "collected at server side", // placeholder
                    userAgent: navigator.userAgent
                };
                localStorage.setItem("privacySignature", JSON.stringify(signatureData));
            } else {
                // When unchecked, hide signature section
                sigSection.classList.add("hidden");
                nextBtn.disabled = true;
                nextBtn.classList.add("opacity-50", "cursor-not-allowed");
                localStorage.removeItem("privacySignature");
            }

            localStorage.setItem("privacyAgreed", String(agreed));
        });

        // ===== SUBMIT =====
        document
            .getElementById("privacyForm")
            .addEventListener("submit", function (e) {
                e.preventDefault();
                if (checkbox.checked) {
                    // Save final consent with timestamp
                    const consentData = {
                        agreed: true,
                        name: fullName,
                        dateAgreed: new Date().toISOString(),
                        formVersion: "1.0"
                    };
                    localStorage.setItem("privacyConsent", JSON.stringify(consentData));

                    window.location.href = "/review/";
                }
            });

        // ===== UPDATE DATE =====
        // Update the date in the signature section
        const dateElement = document.querySelector('.fa-check-circle + span');
        if (dateElement) {
            const options = { year: 'numeric', month: 'long', day: 'numeric' };
            const today = new Date().toLocaleDateString('en-US', options);
            dateElement.textContent = `Electronically signed • ${today}`;
        }
 