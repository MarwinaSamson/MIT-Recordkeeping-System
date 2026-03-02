
        const STEPS = [
            { label: "Personal Details", page: "personal-details.html" },
            {
                label: "Educational Background",
                page: "educational-background.html",
            },
            { label: "Working Student", page: "workingStudent.html" },
            { label: "Documents Upload", page: "documents.html" },
            { label: "Privacy Notice", page: "privacyNotice.html" },
            { label: "Review", page: "review.html" },
        ];
        const CURRENT_STEP = 2;
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
                        ? `<div class="flex-1 h-1 mx-2 rounded ${n < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"
                        }"></div>`
                        : "";
                return `<div class="flex items-center ${i < STEPS.length - 1 ? "flex-1" : ""
                    }"><div class="flex flex-col items-center"><div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all ${cc}">${done ? "✓" : n
                    }</div><span class="text-xs mt-2 text-center hidden sm:block max-w-[80px] ${lc}">${s.label
                    }</span></div>${conn}</div>`;
            }).join("");
        }
        renderProgress();
        // ===== BUILD SECTIONS =====
        const LEVELS = [
            { key: "elementary", title: "Elementary", required: true },
            { key: "secondary", title: "Secondary", required: true },
            { key: "college", title: "College", required: true },
            { key: "graduate", title: "Graduate Studies", required: false },
        ];
        const saved = JSON.parse(
            localStorage.getItem("educationalBackground") || "{}"
        );
        const container = document.getElementById("sections");
        LEVELS.forEach((level) => {
            const d = saved[level.key] || {};
            const reqLabel = level.required
                ? '<span class="text-red-500">*</span>'
                : "";
            const optNote = !level.required
                ? '<span class="text-gray-400 text-sm font-normal ml-1">(if applicable)</span>'
                : "";
            container.innerHTML += `
        <div class="border border-gray-200 rounded-xl p-5 space-y-4 mb-4">
          <h3 class="text-lg font-bold text-brand">${level.title}${optNote}</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-semibold mb-1.5">School Name ${reqLabel}</label>
              <input type="text" name="${level.key}_schoolName" value="${d.schoolName || ""
                }" class="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition" />
              <p class="text-xs text-red-500 mt-1 hidden" data-error="${level.key
                }_schoolName"></p>
            </div>
            <div>
              <label class="block text-sm font-semibold mb-1.5">Degree/Course ${reqLabel}</label>
              <input type="text" name="${level.key}_degree" value="${d.degree || ""
                }" class="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition" />
              <p class="text-xs text-red-500 mt-1 hidden" data-error="${level.key
                }_degree"></p>
            </div>
            <div>
              <label class="block text-sm font-semibold mb-1.5">Year Completed ${reqLabel}</label>
              <input type="number" name="${level.key
                }_yearCompleted" min="1950" max="2030" value="${d.yearCompleted || ""
                }" class="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition" />
              <p class="text-xs text-red-500 mt-1 hidden" data-error="${level.key
                }_yearCompleted"></p>
            </div>
          </div>
        </div>`;
        });

        const optNoteScholarship = '<span class="text-gray-400 text-sm font-normal ml-1">(if applicable)</span>';

            container.innerHTML += `
        <div class="border border-gray-200 rounded-xl p-5 space-y-4 mb-4">
            <h3 class="text-lg font-bold text-brand">Scholarship ${optNoteScholarship}</h3>
            <div>
            <input type="text" name="scholarship" value="${saved.scholarship || ""}"
                class="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand/40 focus:border-brand transition" />
            <p class="text-xs text-red-500 mt-1 hidden" data-error="scholarship"></p>
            </div>
        </div>

        `;

        
        // ===== VALIDATION =====
        document
            .getElementById("eduForm")
            .addEventListener("submit", function (e) {
                e.preventDefault();
                document
                    .querySelectorAll("[data-error]")
                    .forEach((el) => el.classList.add("hidden"));
                let valid = true;
                const data = {};
                LEVELS.forEach((level) => {
                    const sn = this.elements[level.key + "_schoolName"].value.trim();
                    const deg = this.elements[level.key + "_degree"].value.trim();
                    const yr = this.elements[level.key + "_yearCompleted"].value.trim();
                    const scholarship = this.elements["scholarship"].value.trim();
                    data.scholarship = scholarship;
                    
                    data[level.key] = {
                        schoolName: sn,
                        degree: deg,
                        yearCompleted: yr,
                    };
                    if (level.required) {
                        if (!sn) {
                            showError(level.key + "_schoolName", "Required");
                            valid = false;
                        }
                        if (!deg) {
                            showError(level.key + "_degree", "Required");
                            valid = false;
                        }
                        if (!yr) {
                            showError(level.key + "_yearCompleted", "Required");
                            valid = false;
                        }
                    }
                });
                if (valid) {
                    localStorage.setItem("educationalBackground", JSON.stringify(data));
                    window.location.href = "workingStudent.html";
                }
            });
        function showError(f, m) {
            const el = document.querySelector(`[data-error="${f}"]`);
            if (el) {
                el.textContent = m;
                el.classList.remove("hidden");
            }
        }
  