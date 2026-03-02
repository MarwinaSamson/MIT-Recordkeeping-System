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
      const CURRENT_STEP = 1;
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
              ? `<div class="flex-1 h-1 mx-2 rounded ${
                  num < CURRENT_STEP ? "bg-green-500" : "bg-gray-300"
                }"></div>`
              : "";
          return `
          <div class="flex items-center ${
            i < STEPS.length - 1 ? "flex-1" : ""
          }">
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
        "firstName",
        "middleName",
        "lastName",
        "dob",
        "age",
        "gender",
        "civilStatus",
        "contactNumber",
        "email",
        "homeAddress",
      ];
      fields.forEach((f) => {
        if (saved[f]) form.elements[f].value = saved[f];
      });
      // ===== VALIDATION & SUBMIT =====
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        // Clear errors
        document
          .querySelectorAll("[data-error]")
          .forEach((el) => el.classList.add("hidden"));
        let valid = true;
        const data = {};
        fields.forEach((f) => {
          data[f] = form.elements[f].value.trim();
        });
        const required = [
          "firstName","lastName","dob","gender","civilStatus","contactNumber","email","placeOfBirth","religion","ethnicity","nationality","disablity","permanentAddress", "currentAddress", "nameOfParent", "relationship", "parentIncome",

        ];
        required.forEach((f) => {
          if (!data[f]) {
            showError(f, "This field is required");
            valid = false;
          }
        });
        // Email format
        if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
          showError("email", "Invalid email format");
          valid = false;
        }
        if (valid) {
          localStorage.setItem("personalDetails", JSON.stringify(data));
          window.location.href = "educational-background.html";
        }
      });
      function showError(field, msg) {
        const el = document.querySelector(`[data-error="${field}"]`);
        if (el) {
          el.textContent = msg;
          el.classList.remove("hidden");
        }
      }

      //Buttons
      document.getElementById("personalForm").addEventListener("submit", function(event) {
          event.preventDefault(); // Prevent default form submission

          // Redirect to next page
          window.location.href = "educationalBackground.html";
      });

      // age
      const dobInput = document.getElementById("dob");
        const ageInput = document.getElementById("age");

        dobInput.addEventListener("change", function () {
            const birthDate = new Date(this.value);
            const today = new Date();

            if (!this.value) {
              ageInput.value = "";
              return;
            }

            let age = today.getFullYear() - birthDate.getFullYear();
            const m = today.getMonth() - birthDate.getMonth();

            if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
              age--;
            }

            ageInput.value = age >= 0 ? age : "";
          });

          //others (specify)
          document.querySelectorAll("select[data-other-target]").forEach(select => {
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
   