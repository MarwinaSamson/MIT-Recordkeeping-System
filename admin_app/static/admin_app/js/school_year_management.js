// ─── CSRF Helper ─────────────────────────────────────────────────────────────

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    for (const cookie of document.cookie.split(';')) {
      const c = cookie.trim();
      if (c.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(c.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const CSRF_TOKEN = getCookie('csrftoken');

async function postJSON(url, data = {}) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: JSON.stringify(data),
    });
    
    if (!res.ok) {
      console.error(`HTTP Error: ${res.status} ${res.statusText}`);
    }
    
    const responseData = await res.json();
    console.log(`Response from ${url}:`, responseData);
    return responseData;
  } catch (err) {
    console.error(`Fetch error for ${url}:`, err);
    throw err;
  }
}

async function getJSON(url) {
  const res = await fetch(url);
  return res.json();
}

// ─── Utility ──────────────────────────────────────────────────────────────────

function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const toastIcon = document.getElementById('toastIcon');
  const toastText = document.getElementById('toastText');

  const iconMap = { success: 'check-circle', error: 'x-circle', info: 'info' };
  const colorMap = { success: 'text-green-400', error: 'text-red-400', info: 'text-blue-400' };

  toastIcon.setAttribute('data-lucide', iconMap[type] || 'check-circle');
  toastIcon.className = `w-4 h-4 ${colorMap[type] || 'text-green-400'}`;
  toastText.textContent = message;
  toast.classList.remove('hidden');
  lucide.createIcons();

  setTimeout(() => toast.classList.add('hidden'), 3000);
}

// ─── State ────────────────────────────────────────────────────────────────────

let activeSchoolYear = null;  // full object from backend
let currentFilter = 'active'; // current list tab filter

// ─── Init ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  loadSummary();
  renderSchoolYears('active');
  filterArchivedYears();
  // Load semester data if semester tab is visible
  const semesterTab = document.getElementById('sy-tab-semester');
  if (semesterTab && !semesterTab.classList.contains('hidden')) {
    loadSemesterData();
  }
});

// ─── Summary + Active Banner ──────────────────────────────────────────────────

async function loadSummary() {
  const data = await getJSON('/admin-panel/admin/school-years/summary/');

  document.getElementById('activeSchoolYearsCount').textContent = data.active_count;
  document.getElementById('archivedYearsCount').textContent = data.archived_count;
  document.getElementById('upcomingYearsCount').textContent = data.upcoming_count;

  if (data.active_school_year) {
    activeSchoolYear = data.active_school_year;
    document.getElementById('activeSchoolYearName').textContent = activeSchoolYear.name;
    document.getElementById('activeSchoolYearDates').textContent = activeSchoolYear.date_range_display;
  } else {
    activeSchoolYear = null;
    document.getElementById('activeSchoolYearName').textContent = 'None';
    document.getElementById('activeSchoolYearDates').textContent = 'No active school year set.';
  }
}

// ─── Tab Switcher (main tabs) ─────────────────────────────────────────────────

function switchSchoolYearTab(tabId, element) {
  document.querySelectorAll('.sy-tab-content').forEach(tab => tab.classList.add('hidden'));
  document.querySelectorAll('.sy-tab').forEach(tab => {
    tab.classList.remove('text-red-800', 'border-red-800');
    tab.classList.add('text-gray-500', 'border-transparent');
  });

  document.getElementById(`sy-tab-${tabId}`)?.classList.remove('hidden');
  element.classList.remove('text-gray-500', 'border-transparent');
  element.classList.add('text-red-800', 'border-red-800');

  if (tabId === 'archive') filterArchivedYears();

  lucide.createIcons();
}

// ─── School Years List ────────────────────────────────────────────────────────

function filterSchoolYears(status) {
  document.querySelectorAll('.sy-filter-tab').forEach(btn => {
    btn.classList.remove('text-red-700', 'border-red-700');
    btn.classList.add('text-gray-500', 'border-transparent');
  });
  event.target.classList.add('text-red-700', 'border-red-700');
  event.target.classList.remove('text-gray-500', 'border-transparent');

  renderSchoolYears(status);
}

async function renderSchoolYears(status) {
  currentFilter = status;
  const container = document.getElementById('schoolYearsList');
  container.innerHTML = `<p class="text-sm text-gray-400 py-4">Loading...</p>`;

  const data = await getJSON(`/admin-panel/admin/school-years/?status=${status}`);
  const list = data.school_years || [];

  if (!list.length) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-400">
        <i data-lucide="inbox" class="w-10 h-10 mx-auto mb-2 opacity-40"></i>
        <p class="text-sm">No school years found.</p>
      </div>`;
    lucide.createIcons();
    return;
  }

  container.innerHTML = list.map(sy => `
    <div class="border border-gray-200 rounded-xl p-5 hover:shadow-sm transition bg-white">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="text-lg font-semibold text-gray-800">${sy.name}</h3>
          <p class="text-xs text-gray-500 mt-1">
            <i data-lucide="calendar" class="w-3 h-3 inline mr-1"></i>
            ${sy.date_range_display}
          </p>
          ${sy.notes ? `<p class="text-xs text-gray-400 italic mt-1">${sy.notes}</p>` : ''}
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-medium ${
          sy.is_active
            ? 'bg-green-100 text-green-700'
            : sy.status === 'draft'
            ? 'bg-gray-100 text-gray-700'
            : 'bg-blue-100 text-blue-700'
        }">
          ${sy.status_display}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-gray-100">
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Enrollment</p>
          <p class="text-lg font-bold text-gray-800">0</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Status</p>
          <p class="text-sm font-medium text-gray-700">${sy.status_display}</p>
        </div>
      </div>

      <div class="flex gap-2">
        <button onclick="openEditSchoolYearModal(${sy.id})"
          class="flex-1 px-3 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <i data-lucide="edit" class="w-4 h-4"></i>Edit
        </button>
        ${!sy.is_active ? `
        <button onclick="handleActivate(${sy.id})"
          class="flex-1 px-3 py-2 border border-green-200 text-green-700 text-sm font-medium rounded-lg hover:bg-green-50 transition flex items-center justify-center gap-2">
          <i data-lucide="zap" class="w-4 h-4"></i>Set Active
        </button>` : ''}
        <button onclick="openArchiveConfirmModal('${sy.name}', ${sy.id})"
          class="flex-1 px-3 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <i data-lucide="archive" class="w-4 h-4"></i>Archive
        </button>
        ${!sy.is_active ? `
        <button onclick="deleteSchoolYear('${sy.name}', ${sy.id})"
          class="flex-1 px-3 py-2 border border-red-200 text-red-700 text-sm font-medium rounded-lg hover:bg-red-50 transition flex items-center justify-center gap-2">
          <i data-lucide="trash-2" class="w-4 h-4"></i>Delete
        </button>` : ''}
      </div>
    </div>
  `).join('');

  lucide.createIcons();
}

// ─── Create School Year ───────────────────────────────────────────────────────

async function createNewSchoolYear() {
  const name = document.getElementById('newSchoolYearInput').value.trim();
  const status = document.getElementById('enrollmentStatusSelect').value;
  const start_date = document.getElementById('newStartDateInput').value || null;
  const end_date = document.getElementById('newEndDateInput').value || null;
  const notes = document.getElementById('newSchoolYearNotes').value.trim();
  const is_active = document.getElementById('newSchoolYearActive').checked;

  if (!name) {
    showToast('School year name is required (format: YYYY-YYYY)', 'error');
    return;
  }

  try {
    console.log('Creating school year:', { name, status, start_date, end_date, notes, is_active });
    const data = await postJSON('/admin-panel/admin/school-years/create/', { name, status, start_date, end_date, notes, is_active });
    console.log('Response:', data);

    if (!data) {
      showToast('No response from server', 'error');
      return;
    }

    if (data.error) {
      showToast(data.error, 'error');
      return;
    }

    if (data.success) {
      // Clear form
      document.getElementById('newSchoolYearInput').value = '';
      document.getElementById('enrollmentStatusSelect').value = 'draft';
      document.getElementById('newStartDateInput').value = '';
      document.getElementById('newEndDateInput').value = '';
      document.getElementById('newSchoolYearNotes').value = '';
      document.getElementById('newSchoolYearActive').checked = false;

      showToast('New school year created successfully', 'success');
      loadSummary();
      renderSchoolYears(currentFilter);
    }
  } catch (err) {
    console.error('Error creating school year:', err);
    showToast('Error: ' + err.message, 'error');
  }
}

// ─── Edit Modal ───────────────────────────────────────────────────────────────

let editingSchoolYearId = null;

async function openEditSchoolYearModal(id = null) {
  // If no id passed, default to the active school year (called from banner button)
  const targetId = id || (activeSchoolYear ? activeSchoolYear.id : null);
  if (!targetId) {
    showToast('No school year to edit.', 'error');
    return;
  }

  editingSchoolYearId = targetId;

  // Fetch all non-archived years and find the target
  const data = await getJSON('/admin-panel/admin/school-years/');
  const allYears = data.school_years || [];
  let sy = allYears.find(s => s.id === targetId);

  // Fallback to activeSchoolYear object if not found in list
  if (!sy && activeSchoolYear && activeSchoolYear.id === targetId) {
    sy = activeSchoolYear;
  }

  if (!sy) {
    showToast('School year not found.', 'error');
    return;
  }

  document.getElementById('editSchoolYearInput').value = sy.name;
  document.getElementById('editStartDateInput').value = sy.start_date || '';
  document.getElementById('editEndDateInput').value = sy.end_date || '';
  document.getElementById('editEnrollmentStatusSelect').value = sy.status;
  document.getElementById('editSchoolYearNotes').value = sy.notes || '';

  document.getElementById('editSchoolYearModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

function closeEditSchoolYearModal() {
  document.getElementById('editSchoolYearModal').style.display = 'none';
  document.body.style.overflow = 'auto';
  editingSchoolYearId = null;
}

async function saveSchoolYearChanges() {
  if (!editingSchoolYearId) return;

  const name = document.getElementById('editSchoolYearInput').value.trim();
  const start_date = document.getElementById('editStartDateInput').value || null;
  const end_date = document.getElementById('editEndDateInput').value || null;
  const status = document.getElementById('editEnrollmentStatusSelect').value;
  const notes = document.getElementById('editSchoolYearNotes').value.trim();

  if (!name || !start_date || !end_date) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  const data = await postJSON(`/admin-panel/admin/school-years/${editingSchoolYearId}/edit/`, {
    name, status, start_date, end_date, notes,
  });

  if (data.error) {
    showToast(data.error, 'error');
    return;
  }

  closeEditSchoolYearModal();
  showToast('School year updated successfully', 'success');
  loadSummary();
  renderSchoolYears(currentFilter);
}

// ─── Activate ─────────────────────────────────────────────────────────────────

async function handleActivate(id) {
  if (!confirm('Set this as the active school year? The current active year will be deactivated.')) return;

  const data = await postJSON(`/admin-panel/admin/school-years/${id}/activate/`);
  if (data.error) { showToast(data.error, 'error'); return; }

  showToast(data.message, 'success');
  loadSummary();
  renderSchoolYears(currentFilter);
}

// Called by the banner "Manage Enrollment" button — opens edit modal for active year
function toggleEnrollment() {
  if (!activeSchoolYear) { showToast('No active school year.', 'error'); return; }
  openEditSchoolYearModal(activeSchoolYear.id);
}

// ─── Archive ──────────────────────────────────────────────────────────────────

async function openArchiveConfirmModal(name, id) {
  if (!confirm(`Archive school year ${name}? It will be moved to the archive section.`)) return;

  const data = await postJSON(`/admin-panel/admin/school-years/${id}/archive/`);
  if (data.error) { showToast(data.error, 'error'); return; }

  showToast(`${name} has been archived`, 'success');
  loadSummary();
  renderSchoolYears(currentFilter);
  filterArchivedYears();
}

// ─── Delete ───────────────────────────────────────────────────────────────────

async function deleteSchoolYear(name, id) {
  if (!confirm(`Are you sure you want to delete school year ${name}? This action cannot be undone.`)) return;

  const data = await postJSON(`/admin-panel/admin/school-years/${id}/delete/`);
  if (data.error) { showToast(data.error, 'error'); return; }

  showToast('School year deleted', 'success');
  loadSummary();
  renderSchoolYears(currentFilter);
}

// ─── Archive Tab ──────────────────────────────────────────────────────────────

async function filterArchivedYears() {
  const search = document.getElementById('archiveSearch')?.value?.trim() || '';
  const year = document.getElementById('archiveYearFilter')?.value || '';

  const data = await getJSON(`/admin-panel/admin/school-years/archived/?search=${encodeURIComponent(search)}&year=${encodeURIComponent(year)}`);

  document.getElementById('totalArchivedCount').textContent = data.total_archived || 0;
  document.getElementById('archivedStudentsCount').textContent = 0; // extend when enrollment linked
  document.getElementById('lastArchivedUpdate').textContent = data.last_updated
    ? new Date(data.last_updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : '—';

  renderArchivedYears(data.archived_school_years || []);
}

function renderArchivedYears(data) {
  const container = document.getElementById('archivedYearsList');

  if (!data.length) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-400">
        <i data-lucide="inbox" class="w-10 h-10 mx-auto mb-2 opacity-40"></i>
        <p class="text-sm">No archived school years found.</p>
      </div>`;
    lucide.createIcons();
    return;
  }

  container.innerHTML = data.map(sy => `
    <div class="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-sm transition">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-800">${sy.name}</h3>
          <p class="text-xs text-gray-500 mt-1">
            <i data-lucide="calendar" class="w-3 h-3 inline mr-1"></i>
            ${sy.date_range_display}
          </p>
          ${sy.archived_at ? `
          <p class="text-xs text-gray-300 mt-0.5">
            Archived: ${new Date(sy.archived_at).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'})}
          </p>` : ''}
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">Archived</span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 pb-4 border-b border-gray-100">
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Total</p>
          <p class="text-lg font-bold text-gray-800">—</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Promoted</p>
          <p class="text-lg font-bold text-green-600">—</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Retained</p>
          <p class="text-lg font-bold text-orange-600">—</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Incomplete</p>
          <p class="text-lg font-bold text-red-600">—</p>
        </div>
      </div>

      <button onclick="viewArchiveDetails('${sy.name}', ${sy.id})"
        class="w-full px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-sm font-medium rounded-lg transition flex items-center justify-center gap-2">
        <i data-lucide="eye" class="w-4 h-4"></i>View Details
      </button>
    </div>
  `).join('');

  lucide.createIcons();
}

// ─── Archive Detail Modal ─────────────────────────────────────────────────────

function viewArchiveDetails(name, id) {
  document.getElementById('archiveDetailYear').textContent = name;
  // Reset counters — extend when enrollment data is linked to school years
  document.getElementById('archiveEnrollmentCount').textContent = '—';
  document.getElementById('archivePromotedCount').textContent = '—';
  document.getElementById('archiveRetainedCount').textContent = '—';
  document.getElementById('archiveIncompleteCount').textContent = '—';

  document.getElementById('viewArchiveModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

function closeViewArchiveModal() {
  document.getElementById('viewArchiveModal').style.display = 'none';
  document.body.style.overflow = 'auto';
}

function switchArchiveTab(tabId) {
  document.querySelectorAll('.archive-detail-tab-content').forEach(tab => tab.classList.add('hidden'));
  document.querySelectorAll('.archive-detail-tab').forEach(btn => {
    btn.classList.remove('text-red-700', 'border-red-700');
    btn.classList.add('text-gray-500', 'border-transparent');
  });

  document.getElementById(`archive-detail-${tabId}`)?.classList.remove('hidden');
  event.target.classList.remove('text-gray-500', 'border-transparent');
  event.target.classList.add('text-red-700', 'border-red-700');
}

// ─── Export (placeholder) ─────────────────────────────────────────────────────

function exportArchiveData(format) {
  showToast(`Exporting as ${format.toUpperCase()}... (Backend integration needed)`, 'info');
}

function exportArchiveDetails() {
  const year = document.getElementById('archiveDetailYear').textContent;
  showToast(`Exporting ${year} details... (Backend integration needed)`, 'info');
  closeViewArchiveModal();
}




// ─── Semester Management ──────────────────────────────────────────────────────

let currentSemesterConfig = null; // { type: '1st'|'2nd'|'Summer', id: 1|2|3 }

async function loadSemesterData() {
  if (!activeSchoolYear) {
    console.log('No active school year, cannot load semesters');
    return;
  }

  try {
    const data = await getJSON(`/admin-panel/admin/school-years/${activeSchoolYear.id}/semesters/`);
    const semesters = data.semesters || [];
    
    // Update the UI for each semester
    semesters.forEach(sem => {
      updateSemesterUI(sem);
    });

    // Update active semester banner (always call, even if no active semester)
    const activeSemester = semesters.find(s => s.is_active);
    updateActiveSemesterBanner(activeSemester);

    updateSemesterOverviewTable(semesters);
  } catch (err) {
    console.error('Error loading semester data:', err);
  }
}

function updateSemesterUI(semester) {
  const semNum = semester.semester_number;
  const badge = document.getElementById(`semester${semNum}Badge`);
  const dates = document.getElementById(`semester${semNum}Dates`);
  const enrollment = document.getElementById(`semester${semNum}Enrollment`);
  const card = document.getElementById(`semesterCard${semNum}`);
  const activateBtn = document.getElementById(`activateSemester${semNum}Btn`);

  if (!badge || !dates || !enrollment || !card || !activateBtn) return;

  // Update badge
  if (semester.is_active) {
    badge.className = 'px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700';
    badge.textContent = 'Active';
    card.classList.add('border-blue-300');
    activateBtn.classList.add('hidden');
  } else {
    badge.className = 'px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700';
    badge.textContent = semester.is_configured ? 'Configured' : 'Inactive';
    card.classList.remove('border-blue-300');
    activateBtn.classList.remove('hidden');
  }

  // Update dates
  if (semester.start_date && semester.end_date) {
    dates.textContent = `${formatDate(semester.start_date)} - ${formatDate(semester.end_date)}`;
    dates.className = '';
  } else {
    dates.textContent = 'No dates set';
    dates.className = 'text-gray-500';
  }

  // Update enrollment
  enrollment.textContent = semester.enrollment_count || 0;
}

function updateActiveSemesterBanner(semester) {
  const nameMap = { 1: '1st Semester', 2: '2nd Semester', 3: 'Summer' };
  
  if (!semester || !semester.is_active) {
    document.getElementById('activeSemesterName').textContent = 'None Selected';
    document.getElementById('activeSemesterDetails').textContent = 'No active semester set for the current school year.';
    return;
  }
  
  document.getElementById('activeSemesterName').textContent = nameMap[semester.semester_number] || 'Unknown';
  
  let details = '';
  if (semester.start_date && semester.end_date) {
    details = `${formatDate(semester.start_date)} - ${formatDate(semester.end_date)}`;
  }
  if (semester.enrollment_count) {
    details += ` • ${semester.enrollment_count} students enrolled`;
  }
  document.getElementById('activeSemesterDetails').textContent = details || 'Active semester configured without dates';
}

function updateSemesterOverviewTable(semesters) {
  const tbody = document.getElementById('semesterOverviewTable');
  const nameMap = { 1: '1st Semester', 2: '2nd Semester', 3: 'Summer' };

  if (!semesters || semesters.length === 0) {
    tbody.innerHTML = `
      <tr class="border-b border-gray-100">
        <td class="py-3 px-4 text-gray-500" colspan="6">
          No semesters configured for the current school year.
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = semesters.map(sem => `
    <tr class="border-b border-gray-100 hover:bg-gray-50">
      <td class="py-3 px-4 font-medium">${nameMap[sem.semester_number] || sem.name}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-1 rounded-full text-xs font-medium ${
          sem.is_active ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
        }">
          ${sem.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td class="py-3 px-4">${sem.start_date ? formatDate(sem.start_date) : '—'}</td>
      <td class="py-3 px-4">${sem.end_date ? formatDate(sem.end_date) : '—'}</td>
      <td class="py-3 px-4">${sem.enrollment_count || 0}</td>
      <td class="py-3 px-4">
        <button onclick="openSemesterConfigModal('${nameMap[sem.semester_number]}', ${sem.semester_number})"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium">
          <i data-lucide="settings" class="w-4 h-4 inline"></i>
        </button>
      </td>
    </tr>
  `).join('');

  lucide.createIcons();
}

function openSemesterConfigModal(type, semesterId) {
  currentSemesterConfig = { type, id: semesterId };
  document.getElementById('semesterConfigTitle').textContent = type;
  
  // Load existing data if available
  if (activeSchoolYear) {
    getJSON(`/admin-panel/admin/school-years/${activeSchoolYear.id}/semesters/`)
      .then(data => {
        const semester = (data.semesters || []).find(s => s.semester_number === semesterId);
        if (semester) {
          document.getElementById('semesterStartDate').value = semester.start_date || '';
          document.getElementById('semesterEndDate').value = semester.end_date || '';
          document.getElementById('semesterEnrollmentLimit').value = semester.enrollment_limit || '';
          document.getElementById('semesterNotes').value = semester.notes || '';
        }
      })
      .catch(err => console.error('Error loading semester config:', err));
  }

  document.getElementById('semesterConfigModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

function closeSemesterConfigModal() {
  document.getElementById('semesterConfigModal').style.display = 'none';
  document.body.style.overflow = 'auto';
  currentSemesterConfig = null;
  
  // Clear form
  document.getElementById('semesterStartDate').value = '';
  document.getElementById('semesterEndDate').value = '';
  document.getElementById('semesterEnrollmentLimit').value = '';
  document.getElementById('semesterNotes').value = '';
}

async function saveSemesterConfig() {
  if (!currentSemesterConfig || !activeSchoolYear) return;

  const startDate = document.getElementById('semesterStartDate').value;
  const endDate = document.getElementById('semesterEndDate').value;
  const enrollmentLimit = document.getElementById('semesterEnrollmentLimit').value;
  const notes = document.getElementById('semesterNotes').value;

  if (!startDate || !endDate) {
    showToast('Please set both start and end dates', 'error');
    return;
  }

  try {
    const data = await postJSON(
      `/admin-panel/admin/school-years/${activeSchoolYear.id}/semesters/${currentSemesterConfig.id}/configure/`,
      {
        start_date: startDate,
        end_date: endDate,
        enrollment_limit: enrollmentLimit || null,
        notes: notes
      }
    );

    if (data.error) {
      showToast(data.error, 'error');
      return;
    }

    closeSemesterConfigModal();
    showToast(`${currentSemesterConfig.type} semester configured successfully`, 'success');
    loadSemesterData();
  } catch (err) {
    console.error('Error saving semester config:', err);
    showToast('Error saving semester configuration', 'error');
  }
}

// ─── Semester Activation Modal ────────────────────────────────────────────────

let pendingActivation = null; // { type: '1st'|'2nd'|'Summer', id: 1|2|3 }

async function activateSemester(type, semesterId) {
  if (!activeSchoolYear) {
    showToast('No active school year. Please set an active school year first.', 'error');
    return;
  }

  // Show confirmation modal instead of browser confirm
  pendingActivation = { type, id: semesterId };
  
  // Set the semester name in the modal
  document.getElementById('activateSemesterName').textContent = type;
  
  // Check if there's a currently active semester
  try {
    const data = await getJSON(`/admin-panel/admin/school-years/${activeSchoolYear.id}/semesters/`);
    const semesters = data.semesters || [];
    const currentActive = semesters.find(s => s.is_active);
    const currentActiveEl = document.getElementById('activateCurrentSemester');
    const currentActiveNameEl = document.getElementById('currentActiveSemesterName');
    
    if (currentActive) {
      const nameMap = { 1: '1st Semester', 2: '2nd Semester', 3: 'Summer' };
      currentActiveEl.classList.remove('hidden');
      currentActiveNameEl.textContent = nameMap[currentActive.semester_number] || 'Unknown';
    } else {
      currentActiveEl.classList.add('hidden');
    }
  } catch (err) {
    console.error('Error checking current semester:', err);
    document.getElementById('activateCurrentSemester').classList.add('hidden');
  }
  
  // Clear any previous errors
  document.getElementById('activateSemesterError').classList.add('hidden');
  
  // Show the modal
  document.getElementById('activateSemesterModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

function closeActivateSemesterModal() {
  document.getElementById('activateSemesterModal').style.display = 'none';
  document.body.style.overflow = 'auto';
  pendingActivation = null;
}

async function confirmActivateSemester() {
  if (!pendingActivation || !activeSchoolYear) return;
  
  const { type, id } = pendingActivation;
  const errorEl = document.getElementById('activateSemesterError');
  
  try {
    const data = await postJSON(
      `/admin-panel/admin/school-years/${activeSchoolYear.id}/semesters/${id}/activate/`
    );

    if (data.error) {
      errorEl.textContent = data.error;
      errorEl.classList.remove('hidden');
      return;
    }

    closeActivateSemesterModal();
    showToast(`${type} semester activated successfully`, 'success');
    loadSemesterData();
  } catch (err) {
    console.error('Error activating semester:', err);
    errorEl.textContent = 'Error activating semester. Please try again.';
    errorEl.classList.remove('hidden');
  }
}

// Add backdrop click handler for the new modal
document.addEventListener('DOMContentLoaded', function() {
  const activateModal = document.getElementById('activateSemesterModal');
  if (activateModal) {
    activateModal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeActivateSemesterModal();
      }
    });
  }
});

// Update the switchSchoolYearTab function to load semester data when switching to semester tab
const originalSwitchSchoolYearTab = switchSchoolYearTab;
switchSchoolYearTab = function(tabId, element) {
  originalSwitchSchoolYearTab(tabId, element);
  if (tabId === 'semester') {
    loadSemesterData();
  }
};

// Update loadSummary to also load semester data if on semester tab
const originalLoadSummary = loadSummary;
loadSummary = async function() {
  await originalLoadSummary();
  // Check if semester tab is visible and load data if so
  const semesterTab = document.getElementById('sy-tab-semester');
  if (semesterTab && !semesterTab.classList.contains('hidden')) {
    loadSemesterData();
  }
};