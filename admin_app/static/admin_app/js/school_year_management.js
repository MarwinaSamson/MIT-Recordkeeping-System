// School Year Management JavaScript

// Sample data for demonstration (will be replaced with backend data)
const schoolYearsData = {
  active: {
    name: '2027-2028',
    startDate: '2027-08-30',
    endDate: '2028-08-30',
    status: 'active',
    enrollmentStatus: 'enrollment-open',
    enrollment: 0,
    notes: 'Current academic year'
  },
  archived: [
    {
      name: '2026-2027',
      startDate: '2026-06-01',
      endDate: '2027-03-31',
      enrollment: 45,
      promoted: 40,
      retained: 3,
      incomplete: 2,
      status: 'archived'
    },
    {
      name: '2025-2026',
      startDate: '2025-06-01',
      endDate: '2026-03-31',
      enrollment: 38,
      promoted: 35,
      retained: 2,
      incomplete: 1,
      status: 'archived'
    },
    {
      name: '2024-2025',
      startDate: '2024-06-01',
      endDate: '2025-03-31',
      enrollment: 32,
      promoted: 30,
      retained: 2,
      incomplete: 0,
      status: 'archived'
    }
  ],
  upcoming: [
    {
      name: '2028-2029',
      startDate: '2028-08-30',
      endDate: '2029-08-30',
      status: 'draft',
      enrollmentStatus: 'draft',
      enrollment: 0
    }
  ]
};

// Switch between School Year Management tabs
function switchSchoolYearTab(tabId, element) {
  // Hide all tabs
  document.querySelectorAll('.sy-tab-content').forEach(tab => {
    tab.classList.add('hidden');
  });

  // Remove active state from all tab buttons
  document.querySelectorAll('.sy-tab').forEach(tab => {
    tab.classList.remove('text-red-800', 'border-red-800');
    tab.classList.add('text-gray-500', 'border-transparent');
  });

  // Show selected tab
  const tabElement = document.getElementById(`sy-tab-${tabId}`);
  if (tabElement) {
    tabElement.classList.remove('hidden');
  }

  // Set active state to clicked button
  element.classList.remove('text-gray-500', 'border-transparent');
  element.classList.add('text-red-800', 'border-red-800');

  // Re-render icons
  lucide.createIcons();
}

// Filter school years by status
function filterSchoolYears(status) {
  // Update active filter button
  document.querySelectorAll('.sy-filter-tab').forEach(btn => {
    btn.classList.remove('text-red-700', 'border-red-700');
    btn.classList.add('text-gray-500', 'border-transparent');
  });
  event.target.classList.add('text-red-700', 'border-red-700');

  renderSchoolYears(status);
}

// Render school years based on status
function renderSchoolYears(status) {
  const container = document.getElementById('schoolYearsList');
  let data = [];

  if (status === 'active') {
    data = [schoolYearsData.active];
  } else if (status === 'upcoming') {
    data = schoolYearsData.upcoming;
  } else if (status === 'draft') {
    data = schoolYearsData.upcoming.filter(sy => sy.status === 'draft');
  }

  container.innerHTML = data.map(sy => `
    <div class="border border-gray-200 rounded-xl p-5 hover:shadow-sm transition bg-white">
      <div class="flex items-start justify-between mb-3">
        <div>
          <h3 class="text-lg font-semibold text-gray-800">${sy.name}</h3>
          <p class="text-xs text-gray-500 mt-1">
            <i data-lucide="calendar" class="w-3 h-3 inline mr-1"></i>
            ${formatDate(sy.startDate)} – ${formatDate(sy.endDate)}
          </p>
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-medium ${
          sy.status === 'active' 
            ? 'bg-green-100 text-green-700' 
            : sy.status === 'draft'
            ? 'bg-gray-100 text-gray-700'
            : 'bg-blue-100 text-blue-700'
        }">
          ${sy.status === 'active' ? 'Active' : sy.status === 'draft' ? 'Draft' : 'Upcoming'}
        </span>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-4 pb-4 border-b border-gray-100">
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Enrollment</p>
          <p class="text-lg font-bold text-gray-800">${sy.enrollment || 0}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Status</p>
          <p class="text-sm font-medium text-gray-700 capitalize">${sy.enrollmentStatus.replace('-', ' ')}</p>
        </div>
      </div>

      <div class="flex gap-2">
        <button onclick="openEditSchoolYearModal()" class="flex-1 px-3 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <i data-lucide="edit" class="w-4 h-4"></i>Edit
        </button>
        <button onclick="openArchiveConfirmModal('${sy.name}')" class="flex-1 px-3 py-2 border border-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition flex items-center justify-center gap-2">
          <i data-lucide="archive" class="w-4 h-4"></i>Archive
        </button>
        <button onclick="deleteSchoolYear('${sy.name}')" class="flex-1 px-3 py-2 border border-red-200 text-red-700 text-sm font-medium rounded-lg hover:bg-red-50 transition flex items-center justify-center gap-2">
          <i data-lucide="trash-2" class="w-4 h-4"></i>Delete
        </button>
      </div>
    </div>
  `).join('');

  lucide.createIcons();
}

// Filter archived years
function filterArchivedYears() {
  const searchText = document.getElementById('archiveSearch').value.toLowerCase();
  const yearFilter = document.getElementById('archiveYearFilter').value;

  const container = document.getElementById('archivedYearsList');
  const filteredData = schoolYearsData.archived.filter(sy => {
    const matchesSearch = sy.name.toLowerCase().includes(searchText);
    const matchesYear = !yearFilter || sy.name === yearFilter;
    return matchesSearch && matchesYear;
  });

  renderArchivedYears(filteredData);
}

// Render archived years
function renderArchivedYears(data) {
  const container = document.getElementById('archivedYearsList');

  if (data.length === 0) {
    container.innerHTML = `
      <div class="text-center py-8 text-gray-400">
        <i data-lucide="inbox" class="w-10 h-10 mx-auto mb-2 opacity-40"></i>
        <p class="text-sm">No archived school years found.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = data.map(sy => `
    <div class="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-sm transition">
      <div class="flex items-start justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-800">${sy.name}</h3>
          <p class="text-xs text-gray-500 mt-1">
            <i data-lucide="calendar" class="w-3 h-3 inline mr-1"></i>
            ${formatDate(sy.startDate)} – ${formatDate(sy.endDate)}
          </p>
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
          Archived
        </span>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 pb-4 border-b border-gray-100">
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Total</p>
          <p class="text-lg font-bold text-gray-800">${sy.enrollment}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Promoted</p>
          <p class="text-lg font-bold text-green-600">${sy.promoted}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Retained</p>
          <p class="text-lg font-bold text-orange-600">${sy.retained}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Incomplete</p>
          <p class="text-lg font-bold text-red-600">${sy.incomplete}</p>
        </div>
      </div>

      <button onclick="viewArchiveDetails('${sy.name}')" class="w-full px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 text-sm font-medium rounded-lg transition flex items-center justify-center gap-2">
        <i data-lucide="eye" class="w-4 h-4"></i>View Details
      </button>
    </div>
  `).join('');

  lucide.createIcons();
}

// View archive details
function viewArchiveDetails(schoolYear) {
  const archiveData = schoolYearsData.archived.find(sy => sy.name === schoolYear);
  if (!archiveData) return;

  document.getElementById('archiveDetailYear').textContent = schoolYear;
  document.getElementById('archiveEnrollmentCount').textContent = archiveData.enrollment;
  document.getElementById('archivePromotedCount').textContent = archiveData.promoted;
  document.getElementById('archiveRetainedCount').textContent = archiveData.retained;
  document.getElementById('archiveIncompleteCount').textContent = archiveData.incomplete;

  document.getElementById('viewArchiveModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

// Close archive details modal
function closeViewArchiveModal() {
  document.getElementById('viewArchiveModal').style.display = 'none';
  document.body.style.overflow = 'auto';
}

// Switch archive details tabs
function switchArchiveTab(tabId) {
  // Hide all tabs
  document.querySelectorAll('.archive-detail-tab-content').forEach(tab => {
    tab.classList.add('hidden');
  });

  // Remove active state from buttons
  document.querySelectorAll('.archive-detail-tab').forEach(btn => {
    btn.classList.remove('text-red-700', 'border-red-700');
    btn.classList.add('text-gray-500', 'border-transparent');
  });

  // Show selected tab
  document.getElementById(`archive-detail-${tabId}`).classList.remove('hidden');

  // Set active button
  event.target.classList.remove('text-gray-500', 'border-transparent');
  event.target.classList.add('text-red-700', 'border-red-700');
}

// Open edit school year modal
function openEditSchoolYearModal() {
  const sy = schoolYearsData.active;
  document.getElementById('editSchoolYearInput').value = sy.name;
  document.getElementById('editStartDateInput').value = sy.startDate;
  document.getElementById('editEndDateInput').value = sy.endDate;
  document.getElementById('editEnrollmentStatusSelect').value = sy.enrollmentStatus;
  document.getElementById('editSchoolYearNotes').value = sy.notes || '';

  document.getElementById('editSchoolYearModal').style.display = 'flex';
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

// Close edit school year modal
function closeEditSchoolYearModal() {
  document.getElementById('editSchoolYearModal').style.display = 'none';
  document.body.style.overflow = 'auto';
}

// Save school year changes
function saveSchoolYearChanges() {
  const name = document.getElementById('editSchoolYearInput').value;
  const startDate = document.getElementById('editStartDateInput').value;
  const endDate = document.getElementById('editEndDateInput').value;
  const status = document.getElementById('editEnrollmentStatusSelect').value;
  const notes = document.getElementById('editSchoolYearNotes').value;

  if (!name || !startDate || !endDate) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  // Update data
  schoolYearsData.active.name = name;
  schoolYearsData.active.startDate = startDate;
  schoolYearsData.active.endDate = endDate;
  schoolYearsData.active.enrollmentStatus = status;
  schoolYearsData.active.notes = notes;

  // Update display
  document.getElementById('activeSchoolYearName').textContent = name;
  document.getElementById('activeSchoolYearDates').textContent = 
    `${formatDate(startDate)} – ${formatDate(endDate)}`;

  closeEditSchoolYearModal();
  showToast('School year updated successfully', 'success');
  lucide.createIcons();
}

// Create new school year
function createNewSchoolYear() {
  const name = document.getElementById('newSchoolYearInput').value;
  const status = document.getElementById('enrollmentStatusSelect').value;
  const startDate = document.getElementById('newStartDateInput').value;
  const endDate = document.getElementById('newEndDateInput').value;
  const notes = document.getElementById('newSchoolYearNotes').value;

  if (!name || !startDate || !endDate) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  // Add to data
  schoolYearsData.upcoming.push({
    name,
    startDate,
    endDate,
    status,
    enrollmentStatus: status,
    enrollment: 0,
    notes
  });

  // Clear form
  document.getElementById('newSchoolYearInput').value = '';
  document.getElementById('enrollmentStatusSelect').value = 'draft';
  document.getElementById('newStartDateInput').value = '';
  document.getElementById('newEndDateInput').value = '';
  document.getElementById('newSchoolYearNotes').value = '';

  // Refresh display
  filterSchoolYears('upcoming');
  showToast('New school year created successfully', 'success');
}

// Toggle enrollment status
function toggleEnrollment() {
  showToast('Enrollment settings updated', 'success');
}

// Delete school year
function deleteSchoolYear(name) {
  if (confirm(`Are you sure you want to delete school year ${name}? This action cannot be undone.`)) {
    schoolYearsData.upcoming = schoolYearsData.upcoming.filter(sy => sy.name !== name);
    filterSchoolYears('upcoming');
    showToast('School year deleted', 'success');
  }
}

// Archive confirmation
function openArchiveConfirmModal(schoolYear) {
  if (confirm(`Archive school year ${schoolYear}? This will move it to the archive section.`)) {
    // Move from upcoming/draft to archived
    const syIndex = schoolYearsData.upcoming.findIndex(sy => sy.name === schoolYear);
    if (syIndex !== -1) {
      const sy = schoolYearsData.upcoming.splice(syIndex, 1)[0];
      sy.status = 'archived';
      sy.enrollment = 0;
      sy.promoted = 0;
      sy.retained = 0;
      sy.incomplete = 0;
      schoolYearsData.archived.push(sy);
      
      filterSchoolYears('upcoming');
      showToast(`${schoolYear} has been archived`, 'success');
    }
  }
}

// Export archive data
function exportArchiveData(format) {
  if (format === 'excel') {
    showToast('Exporting as Excel... (Backend integration needed)', 'info');
  } else if (format === 'pdf') {
    showToast('Exporting as PDF... (Backend integration needed)', 'info');
  }
}

// Export archive details
function exportArchiveDetails() {
  const year = document.getElementById('archiveDetailYear').textContent;
  showToast(`Exporting ${year} details... (Backend integration needed)`, 'info');
  closeViewArchiveModal();
}

// Utility function to format date
function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// Toast notification
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const toastIcon = document.getElementById('toastIcon');
  const toastText = document.getElementById('toastText');

  const iconMap = {
    'success': 'check-circle',
    'error': 'x-circle',
    'info': 'info'
  };

  const colorMap = {
    'success': 'text-green-400',
    'error': 'text-red-400',
    'info': 'text-blue-400'
  };

  toastIcon.setAttribute('data-lucide', iconMap[type] || 'check-circle');
  toastIcon.className = `w-4 h-4 ${colorMap[type] || 'text-green-400'}`;
  toastText.textContent = message;

  toast.classList.remove('hidden');
  lucide.createIcons();

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  // Initialize the first tab
  renderSchoolYears('active');
  filterArchivedYears();
});
