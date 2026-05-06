// Build DOC_ITEMS dynamically from CMS admission_requirements
// If CMS data is not available, fall back to defaults for display
function buildDocItemsFromCMS() {
  if (!window.ADMISSION_REQUIREMENTS_RAW || !Array.isArray(window.ADMISSION_REQUIREMENTS_RAW)) {
    // Fallback to hardcoded if CMS data unavailable
    return [
      { key: "deansRec", label: "Dean's Recommendation", required: true },
      { key: "tor", label: "Transcript of Records (TOR)", required: true },
      { key: "honorableDismissal", label: "Honorable Dismissal", required: true },
      { key: "psa", label: "PSA Birth Certificate", required: true },
      { key: "gsat", label: "GSAT Result", required: true },
    ];
  }
  
  // Convert CMS format to DOC_ITEMS format
  // CMS format: { title, required, multi_page, field_key, ... }
  // DOC_ITEMS format: { key, label, required }
  return window.ADMISSION_REQUIREMENTS_RAW.map(req => ({
    key: req.field_key || _titleToKey(req.title), // Use field_key if available, else compute
    label: req.title,
    required: req.required || false,
    multiPage: req.multi_page || false,
  }));
}

// Helper: convert title to key (matches backend _title_to_key)
function _titleToKey(title) {
  if (!title) return "";
  let key = title.toLowerCase();
  key = key.replace(/[^a-z0-9]+/g, "_");
  key = key.replace(/^_+|_+$/g, "");
  return key;
}

let DOC_ITEMS = [];

// Initialize DOC_STATUS dynamically from DOC_ITEMS
function initDocStatus() {
  const newStatus = {};
  for (const item of DOC_ITEMS) {
    newStatus[item.key] = {
      status: 'pending',  // Default to pending
      note: 'Awaiting submission.',
      uploaded: false,
    };
  }
  console.log("Initialized DOC_STATUS from DOC_ITEMS:", newStatus);
  return newStatus;
}

let DOC_STATUS = {};
let notifications = [];

async function fetchNotifications() {
  try {
    const response = await fetch("/api/student-notifications/", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const data = await response.json();
      notifications = data.notifications.map((n) => ({
        id: n.id,
        icon: n.icon,
        color: n.color,
        bg: n.bg,
        title: n.title,
        msg: n.message,
        time: n.time,
        read: n.read,
      }));
    } else {
      console.error("Failed to fetch notifications:", response.status);
      notifications = [];
    }
  } catch (error) {
    console.error("Error fetching notifications:", error);
    notifications = [];
  } finally {
    buildNotifications();
    buildNotifPreview();
  }
}
let toastTimer = null,
  isEditing = false,
  currentUploadKey = null;

function getStoredData() {
  return window.mitStudentData || {};
}

function getStudentDocs() {
  const stored = getStoredData();
  if (stored.documentFiles) {
    return stored.documentFiles;
  }
  return JSON.parse(localStorage.getItem("mitDocs") || "{}");
}

function getDocumentUrls() {
  const stored = getStoredData();
  if (stored.documentUrls) {
    return stored.documentUrls;
  }
  return {};
}

function getProfileData() {
  const stored = getStoredData();
  if (stored.personalDetails && Object.keys(stored.personalDetails).length) {
    return stored.personalDetails;
  }
  return JSON.parse(localStorage.getItem("mitPersonal") || "{}");
}

/* THEME */
function toggleTheme() {
  const isDark = document.documentElement.classList.toggle("dark");
  localStorage.setItem("mitTheme", isDark ? "dark" : "light");
  document.getElementById("themeIcon").className = isDark
    ? "fas fa-sun"
    : "fas fa-moon";
}
function initTheme() {
  const saved = localStorage.getItem("mitTheme");
  const prefersDark = window.matchMedia("(prefers-color-scheme:dark)").matches;
  // Default to dark theme unless explicitly saved as light
  if (saved !== "light" && (saved === "dark" || prefersDark || saved === null)) {
    document.documentElement.classList.add("dark");
    document.getElementById("themeIcon").className = "fas fa-sun";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  console.log("DOMContentLoaded event fired");
  // Initialize DOC_ITEMS from CMS data FIRST, before building UI
  DOC_ITEMS = buildDocItemsFromCMS();
  console.log("DOC_ITEMS initialized from CMS:", DOC_ITEMS);
  
  // Initialize DOC_STATUS from DOC_ITEMS
  DOC_STATUS = initDocStatus();
  console.log("DOC_STATUS initialized:", DOC_STATUS);
  
  initTheme();
  loadPersonalData();
  buildMiniDocList();
  buildDocGrid();
  buildStatusSummary();
  // Initialize with empty state first
  document.getElementById("progLabel").textContent = "Loading...";
  fetchNotifications();
  // Fetch actual document status from API immediately
  console.log("About to call fetchDocumentStatus()");
  fetchDocumentStatus();
  fetchDocumentDetails();
  loadProfileFields();
  setFieldsDisabled(true);
  // Start polling every 10 seconds
  statusPollInterval = setInterval(fetchDocumentStatus, 10000);
  console.log("Polling started, interval ID:", statusPollInterval);
});

function greetUser() {
  const stored = getStoredData();
  const p = getProfileData();
  const name =
    stored.fullName ||
    [p.firstName, p.lastName].filter(Boolean).join(" ") ||
    "Noellene Pearl A. Villarcampo";
  const h = new Date().getHours();
  const g =
    h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
  document.getElementById("welcomeName").textContent = `${g}, ${name}.`;
}

function loadPersonalData() {
  const stored = getStoredData();
  const p = getProfileData();
  const full =
    stored.fullName ||
    [p.firstName, p.lastName].filter(Boolean).join(" ") ||
    "Noellene Pearl A. Villarcampo";
  const ini =
    stored.initials ||
    [p.firstName, p.lastName]
      .filter(Boolean)
      .map((n) => n[0])
      .join("")
      .toUpperCase() ||
    "JD";
  document.getElementById("sidebarName").textContent = full;
  ["sidebarAvatar", "topAvatar", "profileAvatarBig"].forEach(
    (id) => (document.getElementById(id).textContent = ini),
  );
  document.getElementById("profileName").textContent = full;
  document.getElementById("profileEmail").textContent =
    stored.email || p.email || "—";
  greetUser();
}

function updateProgress() {
  const docs = getStudentDocs();
  const done = DOC_ITEMS.filter((d) => !!docs[d.key]).length;
  const pct = Math.round((done / DOC_ITEMS.length) * 100);
  document.getElementById("progressPercent").textContent = pct + "%";
  document.getElementById("progBar").style.width = pct + "%";
  document.getElementById("progLabel").textContent =
    `${done} of ${DOC_ITEMS.length} submitted`;
  document.getElementById("progressRing").style.strokeDashoffset =
    283 - (283 * pct) / 100;
  document.getElementById("statDocs").textContent =
    `${done}/${DOC_ITEMS.length}`;
  document.getElementById("statApproved").textContent = Object.values(
    DOC_STATUS,
  ).filter((d) => d.status === "approved").length;
  document.getElementById("statReview").textContent = Object.values(
    DOC_STATUS,
  ).filter((d) => d.status === "review").length;
}

function buildMiniDocList() {
  const docs = getStudentDocs();
  document.getElementById("miniDocList").innerHTML = DOC_ITEMS.map((d) => {
    const u = !!docs[d.key],
      s = DOC_STATUS[d.key] || { status: 'pending', note: '' };
    const sc = u ? pillClass(s.status) : "pill-draft",
      sl = u ? capFirst(s.status) : "Not uploaded";
    const ic = u
      ? s.status === "approved"
        ? "var(--green)"
        : s.status === "rejected"
          ? "var(--red)"
          : "var(--blue)"
      : "#D1D5DB";
    return `<div class="mini-row"><i class="fas ${u ? "fa-check-circle" : "fa-circle"}" style="color:${ic}"></i><span>${d.label}</span><span class="pill ${sc}">${sl}</span></div>`;
  }).join("");
}

function buildDocGrid() {
  const docs = getStudentDocs();
  document.getElementById("docGrid").innerHTML = DOC_ITEMS.map((d) => {
    const u = !!docs[d.key],
      s = DOC_STATUS[d.key] || { status: 'pending', note: '' },
      fn = docs[d.key] || null;
    const sc = u ? pillClass(s.status) : "pill-draft",
      sl = u ? capFirst(s.status) : "Not uploaded";
    const rc = u ? s.status : "";
    const ibg = u
      ? s.status === "approved"
        ? "var(--green-bg)"
        : s.status === "rejected"
          ? "var(--red-light)"
          : "var(--blue-bg)"
      : "var(--rule-light)";
    const ic = u
      ? s.status === "approved"
        ? "var(--green)"
        : s.status === "rejected"
          ? "var(--red)"
          : "var(--blue)"
      : "#D1D5DB";
    const nc =
      s.status === "rejected"
        ? "color:var(--red)"
        : s.status === "approved"
          ? "color:var(--green)"
          : "color:var(--ink-4)";
    const ni =
      s.status === "rejected"
        ? "fa-exclamation-circle"
        : s.status === "approved"
          ? "fa-check-circle"
          : "fa-info-circle";
    const nh =
      u && s.note
        ? `<div class="doc-note" style="${nc}"><i class="fas ${ni}" style="margin-right:4px;font-size:.65rem"></i>${s.note}</div>`
        : "";
    const urls = getDocumentUrls();
    const viewUrl = urls[d.key] || null;
    const viewButton = viewUrl
      ? `<button class="btn btn-secondary btn-xs" onclick="viewDocument('${d.key}')">
            <i class="fas fa-eye" style="font-size:.65rem"></i>View
         </button>`
      : "";
    return `<div class="doc-row ${rc}">
      <div class="doc-icon-wrap" style="background:${ibg}"><i class="fas ${u ? "fa-file-alt" : "fa-file"}" style="color:${ic}"></i></div>
      <div style="flex:1;min-width:0">
        <div class="doc-name">${d.label}${d.required ? '<span style="color:var(--red);margin-left:2px">*</span>' : ""}</div>
        <div class="doc-meta">${fn || "No file uploaded"}</div>${nh}
      </div>
      <div class="doc-actions">
        <span class="pill ${sc}">${sl}</span>
        ${viewButton}
        <button class="btn btn-outline btn-xs" onclick="triggerUploadFor('${d.key}')">
          <i class="fas ${u ? "fa-sync-alt" : "fa-upload"}" style="font-size:.65rem"></i>${u ? "Replace" : "Upload"}
        </button>
      </div>
    </div>`;
  }).join("");
}

function buildStatusSummary() {
  const docs = getStudentDocs();
  const c = { approved: 0, review: 0, rejected: 0, pending: 0 };
  DOC_ITEMS.forEach((d) => {
    if (!!docs[d.key]) {
      const status = (DOC_STATUS[d.key] || {}).status || 'pending';
      c[status]++;
    } else {
      c["pending"]++;
    }
  });
  document.getElementById("statusSummary").innerHTML = [
    {
      key: "approved",
      label: "Approved",
      icon: "fa-check-circle",
      color: "var(--green)",
    },
    {
      key: "review",
      label: "Under Review",
      icon: "fa-search",
      color: "var(--blue)",
    },
    {
      key: "rejected",
      label: "Rejected",
      icon: "fa-times-circle",
      color: "var(--red)",
    },
    {
      key: "pending",
      label: "Not Uploaded",
      icon: "fa-circle",
      color: "#D1D5DB",
    },
  ]
    .map(
      (
        i,
      ) => `<div style="display:flex;align-items:center;gap:9px;padding:5px 0;border-bottom:1px solid var(--rule-light)">
    <i class="fas ${i.icon}" style="color:${i.color};width:14px;font-size:.75rem;flex-shrink:0"></i>
    <span style="font-size:.79rem;color:var(--ink-3);flex:1">${i.label}</span>
    <span style="font-size:.82rem;font-weight:700;color:var(--ink)">${c[i.key]}</span>
  </div>`,
    )
    .join("");
}

function buildNotifications() {
  const u = notifications.filter((n) => !n.read).length;
  document.getElementById("notifBadge").textContent = u || "";
  document.getElementById("notifBadge").style.display = u ? "" : "none";
  document.getElementById("topNotifDot").style.display = u ? "block" : "none";
  document.getElementById("notifList").innerHTML = notifications.length
    ? notifications.map((n) => renderN(n)).join("")
    : `<div style="text-align:center;padding:32px 0;color:var(--ink-4);font-size:.82rem">No notifications</div>`;
}

function buildNotifPreview() {
  document.getElementById("notifPreview").innerHTML = notifications
    .slice(0, 3)
    .map((n) => renderN(n, true))
    .join("");
}

function renderN(n, compact = false) {
  return `<div class="notif-item ${n.read ? "" : "unread"}" onclick="readNotif(${n.id})">
    <div class="notif-icon-wrap" style="background:${n.bg}"><i class="fas ${n.icon}" style="color:${n.color}"></i></div>
    <div style="flex:1;min-width:0">
      <div class="notif-title">${n.title}${!n.read ? '<span class="notif-dot"></span>' : ""}</div>
      <div class="notif-msg" ${compact ? 'style="display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden"' : ""}>${n.msg}</div>
      <div class="notif-time">${n.time}</div>
    </div>
  </div>`;
}

function readNotif(id) {
  // Call API to mark notification as read
  fetch("/api/notifications/read/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ notification_id: id }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        notifications = notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n,
        );
        buildNotifications();
        buildNotifPreview();
      }
    })
    .catch((error) => console.error("Error marking notification as read:", error));
}

function markAllRead() {
  // Call API to mark all notifications as read
  fetch("/api/notifications/read-all/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        notifications = notifications.map((n) => ({ ...n, read: true }));
        buildNotifications();
        buildNotifPreview();
        showToast("All notifications marked as read");
      }
    })
    .catch((error) => console.error("Error marking all notifications as read:", error));
}

function triggerUploadFor(key) {
  currentUploadKey = key;
  document.getElementById("fileInput").click();
}
function handleFileSelect(e) {
  const f = e.target.files[0];
  if (f) processUpload(f);
  e.target.value = "";
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.remove("dragover");
  const f = e.dataTransfer.files[0];
  if (f) processUpload(f);
}

function processUpload(file) {
  if (file.size > 10 * 1024 * 1024) {
    showToast("File exceeds 10 MB limit", "error");
    return;
  }
  const docs = JSON.parse(localStorage.getItem("mitDocs") || "{}");
  if (currentUploadKey) {
    docs[currentUploadKey] = file.name;
    currentUploadKey = null;
  } else {
    const m = DOC_ITEMS.find((d) => !docs[d.key]);
    if (!m) {
      showToast("All documents uploaded. Use Replace to swap.", "info");
      return;
    }
    docs[m.key] = file.name;
  }
  localStorage.setItem("mitDocs", JSON.stringify(docs));
  buildDocGrid();
  buildMiniDocList();
  buildStatusSummary();
  updateProgress();
  const no = document.getElementById("uploadNotice");
  document.getElementById("uploadNoticeTxt").textContent =
    `"${file.name}" uploaded successfully`;
  no.classList.remove("hidden");
  setTimeout(() => no.classList.add("hidden"), 4500);
  showToast(`"${file.name}" uploaded`);
}

function loadProfileFields() {
  const stored = getStoredData();
  const p = getProfileData();

  if (p.firstName) document.getElementById("pFirstName").value = p.firstName;
  if (p.lastName) document.getElementById("pLastName").value = p.lastName;
  if (p.dob) document.getElementById("pDob").value = p.dob;
  if (p.gender) document.getElementById("pGender").value = p.gender;
  if (p.contact) document.getElementById("pContact").value = p.contact;
  if (p.email) document.getElementById("pEmail").value = p.email;
  if (p.address) document.getElementById("pAddress").value = p.address;

  if (stored.education && stored.education.college) {
    document.getElementById("profileCollege").textContent =
      stored.education.college;
  }
  if (stored.education && stored.education.graduate) {
    document.getElementById("profileGrad").textContent =
      stored.education.graduate;
  }
}

function setFieldsDisabled(d) {
  [
    "pFirstName",
    "pLastName",
    "pDob",
    "pGender",
    "pContact",
    "pEmail",
    "pAddress",
  ].forEach((id) => {
    document.getElementById(id).disabled = d;
  });
}

function toggleEditMode() {
  isEditing = !isEditing;
  setFieldsDisabled(!isEditing);
  document.getElementById("editBtnLabel").textContent = isEditing
    ? "Cancel"
    : "Edit Profile";
  document.getElementById("savePersonalBtns").style.display = isEditing
    ? "flex"
    : "none";
  document.getElementById("editIndicator").style.display = isEditing
    ? "block"
    : "none";
}

function cancelEdit() {
  isEditing = false;
  setFieldsDisabled(true);
  document.getElementById("editBtnLabel").textContent = "Edit Profile";
  document.getElementById("savePersonalBtns").style.display = "none";
  document.getElementById("editIndicator").style.display = "none";
  loadProfileFields();
}

function saveProfile() {
  const p = {
    firstName: document.getElementById("pFirstName").value.trim(),
    lastName: document.getElementById("pLastName").value.trim(),
    dob: document.getElementById("pDob").value,
    gender: document.getElementById("pGender").value,
    contact: document.getElementById("pContact").value.trim(),
    email: document.getElementById("pEmail").value.trim(),
    address: document.getElementById("pAddress").value.trim(),
  };
  localStorage.setItem("mitPersonal", JSON.stringify(p));
  loadPersonalData();
  loadProfileFields();
  isEditing = false;
  setFieldsDisabled(true);
  document.getElementById("editBtnLabel").textContent = "Edit Profile";
  document.getElementById("savePersonalBtns").style.display = "none";
  document.getElementById("editIndicator").style.display = "none";
  showToast("Profile updated successfully");
}

const PAGE_META = {
  overview: { breadcrumb: "Dashboard", title: "Overview" },
  documents: { breadcrumb: "Dashboard", title: "My Documents" },
  notifications: { breadcrumb: "Dashboard", title: "Notifications" },
  profile: { breadcrumb: "Account", title: "My Profile" },
};

function viewDocument(key) {
  const urls = getDocumentUrls();
  const url = urls[key];
  if (!url) {
    showToast("No document preview available for this item.");
    return;
  }

  const title = DOC_ITEMS.find((item) => item.key === key)?.label || "Document";
  const iframe = document.getElementById("docPreviewFrame");
  const img = document.getElementById("docPreviewImage");
  const fallback = document.getElementById("docPreviewFallback");
  const downloadLink = document.getElementById("docPreviewDownloadLink");

  document.getElementById("docPreviewTitle").textContent = `Preview: ${title}`;
  if (downloadLink) {
    downloadLink.href = url;
  }

  const isImage = /\.(jpe?g|png|gif|bmp|webp)(\?|$)/i.test(url);
  const isPdf = /\.pdf(\?|$)/i.test(url);

  if (isPdf) {
    iframe.src = url;
    iframe.style.display = "block";
    img.style.display = "none";
    fallback.style.display = "none";
  } else if (isImage) {
    img.src = url;
    img.style.display = "block";
    iframe.style.display = "none";
    fallback.style.display = "none";
  } else {
    iframe.style.display = "none";
    img.style.display = "none";
    fallback.style.display = "block";
  }

  document.getElementById("docPreviewModal").style.display = "flex";
}

function closeDocPreview() {
  const iframe = document.getElementById("docPreviewFrame");
  const img = document.getElementById("docPreviewImage");
  iframe.src = "";
  img.src = "";
  document.getElementById("docPreviewModal").style.display = "none";
}

function switchPage(pageId, el) {
  document
    .querySelectorAll(".page")
    .forEach((p) => p.classList.remove("active"));
  document.getElementById("page-" + pageId).classList.add("active");
  document
    .querySelectorAll(".nav-item")
    .forEach((n) => n.classList.remove("active"));
  if (el) el.classList.add("active");
  const m = PAGE_META[pageId] || { breadcrumb: "", title: "" };
  document.getElementById("topBreadcrumb").textContent = m.breadcrumb;
  document.getElementById("topTitle").textContent = m.title;
  if (pageId === "overview") {
    buildMiniDocList();
    buildNotifPreview();
    // Re-fetch latest data from API to ensure accuracy
    fetchDocumentStatus();
  }
  if (pageId === "documents") {
    buildDocGrid();
    buildStatusSummary();
  }
  if (pageId === "notifications") fetchNotifications();
  if (pageId === "profile") loadProfileFields();
  closeSidebar();
  window.scrollTo(0, 0);
}

function toggleSidebar() {
  document.getElementById("sidebar").classList.toggle("open");
  document.getElementById("overlay").classList.toggle("active");
}
function closeSidebar() {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("overlay").classList.remove("active");
}
function handleLogout() {
  if (confirm("Sign out of MIT Student Portal?")) {
    window.location.href = "/logout/";
  }
}

function showToast(msg, type = "success") {
  const c = { success: "#4ADE80", error: "#F87171", info: "#60A5FA" };
  const i = {
    success: "fa-check-circle",
    error: "fa-exclamation-circle",
    info: "fa-info-circle",
  };
  document.getElementById("toastText").textContent = msg;
  document.getElementById("toastIcon").style.color = c[type];
  document.getElementById("toastIcon").className = `fas ${i[type]}`;
  const t = document.getElementById("toast");
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 3500);
}

function pillClass(s) {
  return (
    {
      approved: "pill-approved",
      review: "pill-review",
      rejected: "pill-rejected",
      pending: "pill-pending",
      draft: "pill-draft",
    }[s] || "pill-draft"
  );
}
function capFirst(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : "";
}

/* POLLING: Check for document status updates */
let statusPollInterval = null;
let cachedStatus = {
  verified_documents: null,
  reviewing_documents: null,
  application_status: null,
  submission_deadline: null,
};

function fetchDocumentDetails() {
  console.log("🔍 fetchDocumentDetails() CALLED");
  // Fetch detailed document statuses from server and update DOC_STATUS
  fetch("/api/document-details/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((res) => {
      console.log("🔍 API response received, status:", res.status);
      return res.json();
    })
    .then((docDetails) => {
      console.log("=== API RESPONSE ===");
      console.log("Raw API response:", docDetails);
      console.log("API response keys:", Object.keys(docDetails));
      
      // Update DOC_STATUS with actual database values
      for (const key in docDetails) {
        const detail = docDetails[key];
        console.log(`Processing API key "${key}":`, detail);
        
        // Create entry if it doesn't exist yet (happens when API returns new keys)
        if (!DOC_STATUS[key]) {
          DOC_STATUS[key] = {
            status: 'pending',
            note: '',
            uploaded: false,
          };
        }
        
        // Map verification status to display status
        // 'approved' = verified and approved
        // 'review' = currently reviewing
        // 'pending' = waiting for review
        // 'rejected' = rejected, needs resubmission
        DOC_STATUS[key].status = detail.status;
        DOC_STATUS[key].uploaded = detail.uploaded || false;
        
        if (detail.rejection_reason) {
          DOC_STATUS[key].note = detail.rejection_reason;
        } else if (detail.remarks) {
          DOC_STATUS[key].note = detail.remarks;
        }
        
        console.log(`✓ Updated DOC_STATUS[${key}]:`, DOC_STATUS[key]);
      }
      console.log("Final DOC_STATUS after API update:", DOC_STATUS);
      console.log("=== END API RESPONSE ===");
      
      
      // Rebuild UI with updated statuses
      buildMiniDocList();
      buildDocGrid();
      buildStatusSummary();
    })
    .catch((err) => {
      console.error("❌ Error fetching document details:", err);
      console.error("Error details:", err.message);
    });
}

function fetchDocumentStatus() {
  console.log("Starting fetchDocumentStatus...");
  fetch("/api/document-status/", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((res) => {
      console.log("API Response status:", res.status);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then((data) => {
      console.log("Document status data:", data);
      
      // Check if any values changed
      const changed = {
        verified: cachedStatus.verified_documents !== data.verified_documents,
        reviewing:
          cachedStatus.reviewing_documents !== data.reviewing_documents,
        status: cachedStatus.application_status !== data.application_status,
        deadline:
          cachedStatus.submission_deadline !== data.submission_deadline,
      };

      // On first load, always update (when cached values are null)
      const isFirstLoad = cachedStatus.verified_documents === null;

      if (isFirstLoad || changed.verified || changed.reviewing || changed.status || changed.deadline) {
        // Update cached values
        cachedStatus = data;

        // Update approved documents count
        if (isFirstLoad || changed.verified) {
          const statApprovedEl = document.getElementById("statApproved");
          console.log("statApproved element:", statApprovedEl);
          if (statApprovedEl) {
            statApprovedEl.textContent = data.verified_documents;
          }
          // Also update progress based on verified count
          if (data.total_documents > 0) {
            const progressPercent = Math.round((data.verified_documents / data.total_documents) * 100);
            console.log("Updating progress to:", progressPercent + "%");
            const progressPercentEl = document.getElementById("progressPercent");
            const progBarEl = document.getElementById("progBar");
            const progressRingEl = document.getElementById("progressRing");
            const progLabelEl = document.getElementById("progLabel");
            
            console.log("Elements found - progressPercent:", !!progressPercentEl, "progBar:", !!progBarEl, "progressRing:", !!progressRingEl, "progLabel:", !!progLabelEl);
            
            if (progressPercentEl) progressPercentEl.textContent = progressPercent + "%";
            if (progBarEl) progBarEl.style.width = progressPercent + "%";
            if (progressRingEl) progressRingEl.style.strokeDashoffset = 283 - (283 * progressPercent) / 100;
            if (progLabelEl) progLabelEl.textContent = `${data.verified_documents} of ${data.total_documents} completed`;
          }
        }

        // Update reviewing documents count
        if (isFirstLoad || changed.reviewing) {
          document.getElementById("statReview").textContent =
            data.reviewing_documents;
        }

        // Update application status in banner
        if (isFirstLoad || changed.status) {
          const statusChip = document.getElementById("statusChip");
          if (statusChip) {
            const statusText = data.application_status.charAt(0).toUpperCase() + 
                              data.application_status.slice(1).toLowerCase();
            statusChip.innerHTML = `<i
                  class="fas fa-circle"
                  style="font-size: 0.5rem; color: var(--green)"
                ></i
                >Status: ${statusText}`;
          }
        }

        // Update submission deadline
        if (isFirstLoad || changed.deadline) {
          const dateRows = document.querySelectorAll(".date-row");
          dateRows.forEach((row) => {
            const label = row.querySelector(".date-label");
            if (
              label &&
              label.textContent.includes("Document Submission Deadline")
            ) {
              row.querySelector(".date-val").textContent =
                data.submission_deadline;
            }
          });
        }

        // Show notifications for important changes
        if (
          !isFirstLoad &&
          changed.verified &&
          data.verified_documents >
            (cachedStatus.verified_documents - 1 || -1)
        ) {
          showToast(
            `✓ Document verified! ${data.verified_documents} approved.`,
            "success",
          );
        } else if (changed.reviewing) {
          showToast(
            `📋 ${data.reviewing_documents} document(s) under review.`,
            "info",
          );
        }

        if (changed.status) {
          showToast(
            `Application status: ${data.application_status}`,
            "info",
          );
        }

        // Fetch updated document details
        fetchDocumentDetails();
      }
    })
    .catch((err) => {
      console.error("Error fetching document status:", err);
    });
}

function startStatusPolling() {
  // Fetch document details immediately on load
  fetchDocumentDetails();
  // Fetch status immediately on load
  fetchDocumentStatus();
  // Then poll every 10 seconds
  statusPollInterval = setInterval(fetchDocumentStatus, 10000);
}

function stopStatusPolling() {
  if (statusPollInterval) {
    clearInterval(statusPollInterval);
    statusPollInterval = null;
  }
}

// Stop polling when user leaves the page
window.addEventListener("beforeunload", () => {
  stopStatusPolling();
});