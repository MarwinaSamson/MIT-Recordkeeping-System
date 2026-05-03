/**
 * admin_cms_scripts.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Dedicated JS for the CMS Settings page (cms_settings.html).
 * Handles all tab switching, CMS CRUD, faculty management, carousel, etc.
 * Depends on: lucide (global), Django CSRF cookie
 * ─────────────────────────────────────────────────────────────────────────────
 */

'use strict';

/* ══════════════════════════════════════════════════════════════
   CSRF HELPER
══════════════════════════════════════════════════════════════ */
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let c of cookies) {
    const trimmed = c.trim();
    if (trimmed.startsWith(name + '=')) {
      return decodeURIComponent(trimmed.substring(name.length + 1));
    }
  }
  return '';
}

/* ══════════════════════════════════════════════════════════════
   TOAST NOTIFICATION
══════════════════════════════════════════════════════════════ */
let _toastTimer = null;

function showCmsToast(msg, type = 'success') {
  const toast  = document.getElementById('cmsToast');
  const icon   = document.getElementById('cmsToastIcon');
  const text   = document.getElementById('cmsToastText');
  if (!toast) return;

  text.textContent = msg;
  icon.setAttribute('data-lucide', type === 'success' ? 'check-circle' : 'alert-triangle');
  toast.className = 'show ' + type;
  lucide.createIcons();

  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toast.classList.remove('show'), 3400);
}

/* ══════════════════════════════════════════════════════════════
   TOP-LEVEL TAB SWITCHING  (Account / Teacher / Content / History / Others)
══════════════════════════════════════════════════════════════ */
function switchTopTab(name, btn) {
  document.querySelectorAll('.top-panel').forEach(p => p.classList.add('hidden'));
  document.querySelectorAll('.settings-top-tab').forEach(b => {
    b.classList.remove('border-red-800', 'text-red-800');
    b.classList.add('border-transparent', 'text-gray-500');
  });
  const panel = document.getElementById('top-' + name);
  if (panel) panel.classList.remove('hidden');
  btn.classList.remove('border-transparent', 'text-gray-500');
  btn.classList.add('border-red-800', 'text-red-800');
}

/* ══════════════════════════════════════════════════════════════
   CMS CONTENT SUB-TAB SWITCHING  (Homepage / Announcement / Carousel …)
══════════════════════════════════════════════════════════════ */
function switchCmsTab(name, btn) {
  document.querySelectorAll('.cms-panel').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  document.querySelectorAll('.cms-tab').forEach(b => b.classList.remove('active'));

  const panel = document.getElementById('cms-' + name);
  if (panel) {
    panel.classList.remove('hidden');
    panel.classList.add('active');
  }
  btn.classList.add('active');

  // Lazy-load faculty when that tab is opened
  if (name === 'faculty-cms') loadFaculty();
  lucide.createIcons();
}

/* ══════════════════════════════════════════════════════════════
   ABOUT PAGE INNER TABS  (Program Info / Objectives / Outcomes …)
══════════════════════════════════════════════════════════════ */
function switchAboutTab(name, btn) {
  document.querySelectorAll('.about-panel').forEach(p => p.classList.add('hidden'));
  document.querySelectorAll('.about-tab').forEach(b => {
    b.classList.remove('border-red-800', 'text-red-800');
    b.classList.add('border-transparent', 'text-gray-400');
  });
  const panel = document.getElementById('about-tab-' + name);
  if (panel) panel.classList.remove('hidden');
  btn.classList.remove('border-transparent', 'text-gray-400');
  btn.classList.add('border-red-800', 'text-red-800');
}

/* ══════════════════════════════════════════════════════════════
   OTHERS SUB-TAB SWITCHING  (Position / Department / Grade Level …)
══════════════════════════════════════════════════════════════ */
function switchOthersTab(name, btn) {
  // Hide all others panels
  document.querySelectorAll('.others-panel').forEach(p => p.classList.add('hidden'));
  // Deactivate all others-scoped tabs (buttons that call this function)
  const othersContainer = document.getElementById('top-others');
  if (othersContainer) {
    othersContainer.querySelectorAll('.cms-tab').forEach(b => b.classList.remove('active'));
  }
  // Show target panel
  const panel = document.getElementById('others-' + name);
  if (panel) panel.classList.remove('hidden');
  btn.classList.add('active');
  lucide.createIcons();
}

/* ══════════════════════════════════════════════════════════════
   HOMEPAGE & ANNOUNCEMENT CMS
══════════════════════════════════════════════════════════════ */

/** Add a blank announcement row */
function addAnnouncementRow() {
  const list = document.getElementById('announcementsList');
  if (!list) return;
  const div = document.createElement('div');
  div.className = 'announcement-row flex items-center gap-3';
  div.innerHTML = `
    <input type="text" placeholder="Announcement text…" class="ann-text field flex-1" />
    <div class="flex items-center gap-1.5 flex-shrink-0">
      <input type="number" placeholder="sec" value="5" min="3" max="30"
        class="ann-duration field text-center" style="width:64px;" />
      <span class="text-xs text-gray-400">sec</span>
    </div>
    <button type="button" onclick="removeAnnouncementRow(this)" class="btn-del">
      <i data-lucide="x"></i>
    </button>`;
  list.appendChild(div);
  lucide.createIcons();
}

/** Remove an announcement row (keep at least 1) */
function removeAnnouncementRow(btn) {
  const list = document.getElementById('announcementsList');
  if (list && list.querySelectorAll('.announcement-row').length > 1) {
    btn.closest('.announcement-row').remove();
  }
}

/** Save announcement settings via CMS API */
async function saveAnnouncementSettings() {
  const announcements = _collectAnnouncements();
  const showAnn = document.getElementById('cmsAnnouncementToggle')?.classList.contains('on');
  if (showAnn && announcements.length === 0) {
    showCmsToast('Add at least one announcement, or disable the bar.', 'error');
    return;
  }
  await _postCMS({ show_announcement: showAnn, announcements });
}

/** Save homepage hero + deadline settings */
async function saveHomepageSettings() {
  await _postCMS({
    admissions_open:      document.getElementById('cmsAdmissionsToggle')?.classList.contains('on'),
    show_announcement:    document.getElementById('cmsAnnouncementToggle')?.classList.contains('on'),
    nav_subtitle:         document.getElementById('cmsNavSubtitle')?.value.trim() || '',
    hero_badge:           document.getElementById('cmsHeroBadge')?.value.trim() || '',
    hero_heading1:        document.getElementById('cmsHeroHeading1')?.value.trim() || '',
    hero_heading2:        document.getElementById('cmsHeroHeading2')?.value.trim() || '',
    hero_tagline:         document.getElementById('cmsHeroTagline')?.value.trim() || '',
    application_deadline: document.getElementById('cmsDeadline')?.value || null,
  });
}

/** Live-preview the seal/logo before saving */
function previewSeal(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  if (file.size > 2 * 1024 * 1024) { showCmsToast('Seal image must be under 2 MB.', 'error'); return; }
  const reader = new FileReader();
  reader.onload = e => {
    const wrap = document.getElementById('sealPreviewWrap');
    const icon = document.getElementById('sealPreviewIcon');
    if (icon) icon.style.display = 'none';
    let img = document.getElementById('sealPreviewImg');
    if (!img) {
      img = document.createElement('img');
      img.id = 'sealPreviewImg';
      img.className = 'w-full h-full object-contain';
      wrap.appendChild(img);
    }
    img.src = e.target.result;
    // Upload immediately via existing upload endpoint
    const formData = new FormData();
    formData.append('file', file);
    formData.append('field', 'site_seal');
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    fetch('/admin/api/cms/upload-file/', { method: 'POST', body: formData })
      .then(r => r.json())
      .then(d => { if (d.success) showCmsToast('Seal uploaded!', 'success'); else showCmsToast(d.message || 'Upload failed.', 'error'); })
      .catch(() => showCmsToast('Upload error.', 'error'));
  };
  reader.readAsDataURL(file);
}

/** Save programs list settings */
async function saveProgramsSettings() {
  const programs = [];
  document.querySelectorAll('.program-row').forEach(row => {
    const name        = row.querySelector('.prog-name')?.value.trim()  || '';
    const degree      = row.querySelector('.prog-degree')?.value.trim()|| '';
    const description = row.querySelector('.prog-desc')?.value.trim()  || '';
    const visible     = row.querySelector('.prog-visible-toggle')?.classList.contains('on') ?? true;
    if (name) programs.push({ name, degree, description, visible });
  });
  await _postCMS({ programs });
}

/** Core CMS POST helper */
async function _postCMS(payload) {
  try {
    const res = await fetch('/admin/api/cms/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.success) {
      showCmsToast('Settings saved!', 'success');
    } else {
      showCmsToast('Error: ' + (data.message || 'Save failed.'), 'error');
    }
  } catch {
    showCmsToast('Network error. Please try again.', 'error');
  }
}

function _collectAnnouncements() {
  const rows = [];
  document.querySelectorAll('.announcement-row').forEach(row => {
    const text     = row.querySelector('.ann-text')?.value.trim()  || '';
    const duration = parseInt(row.querySelector('.ann-duration')?.value) || 5;
    if (text) rows.push({ text, duration: Math.max(3, duration) });
  });
  return rows;
}

/* ══════════════════════════════════════════════════════════════
   PROGRAMS LIST (cms-programs-list panel)
══════════════════════════════════════════════════════════════ */
function addProgramRow() {
  const list = document.getElementById('programsList');
  if (!list) return;
  const div = document.createElement('div');
  div.className = 'row-card program-row';
  div.innerHTML = `
    <div class="flex items-center gap-2 mb-3">
      <input type="text" placeholder="Program name e.g. Master in Information Technology"
        class="prog-name field flex-1" />
      <button type="button" onclick="removeProgramRow(this)" class="btn-del">
        <i data-lucide="x"></i>
      </button>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
      <input type="text" placeholder="Degree type e.g. Master's Degree" class="prog-degree field" />
      <textarea placeholder="Short description…" rows="2" class="prog-desc field"></textarea>
    </div>
    <div class="flex items-center gap-2">
      <div class="toggle-track on prog-visible-toggle" onclick="this.classList.toggle('on')">
        <div class="toggle-thumb"></div>
      </div>
      <span class="text-xs text-gray-500 font-medium">Visible on homepage</span>
    </div>`;
  list.appendChild(div);
  lucide.createIcons();
}

function removeProgramRow(btn) {
  btn.closest('.program-row').remove();
}

/* ══════════════════════════════════════════════════════════════
   DOWNLOADS (cms-downloads panel)
══════════════════════════════════════════════════════════════ */
function removeDownloadRow(btn) {
  btn.closest('.download-row').remove();
}

function _initDownloadsUpload() {
  const btn   = document.getElementById('uploadDownloadBtn');
  const input = document.getElementById('downloadFileInput');
  if (!btn || !input) return;

  btn.addEventListener('click', () => input.click());
  input.addEventListener('change', async function () {
    if (!this.files[0]) return;
    const file     = this.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const origHTML = btn.innerHTML;
    btn.disabled   = true;
    btn.innerHTML  = '<i data-lucide="loader" class="w-3.5 h-3.5" style="animation:spin 1s linear infinite"></i> Uploading…';
    lucide.createIcons();

    try {
      const res  = await fetch('/admin/api/cms/upload-file/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() },
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        _appendDownloadRow(data.data || { name: file.name, url: '', file_type: file.name.split('.').pop().toUpperCase() });
        showCmsToast('File uploaded!', 'success');
      } else {
        showCmsToast('Upload error: ' + data.message, 'error');
      }
    } catch {
      showCmsToast('Network error during upload.', 'error');
    } finally {
      btn.disabled  = false;
      btn.innerHTML = origHTML;
      this.value    = '';
      lucide.createIcons();
    }
  });
}

function _appendDownloadRow(file) {
  const list = document.getElementById('downloadsList');
  if (!list) return;
  // Remove "no downloads" placeholder if present
  list.querySelectorAll('p.text-gray-400').forEach(p => p.remove());

  const ext = (file.file_type || '').toUpperCase() || file.name.split('.').pop().toUpperCase();
  const div = document.createElement('div');
  div.className = 'download-row flex items-center gap-3 row-card';
  div.innerHTML = `
    <div class="w-9 h-9 rounded-lg bg-red-100 flex items-center justify-center flex-shrink-0 text-xs font-bold text-red-700">
      ${ext}
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-gray-800 truncate">${file.name}</p>
      <p class="text-xs text-gray-400 truncate">${file.url || ''}</p>
    </div>
    <button type="button" onclick="removeDownloadRow(this)" class="btn-del">
      <i data-lucide="x"></i>
    </button>`;
  list.appendChild(div);
  lucide.createIcons();
}

/* ══════════════════════════════════════════════════════════════
   CAROUSEL SLIDES
══════════════════════════════════════════════════════════════ */
function triggerSlideUpload(n) {
  document.getElementById('slideFile' + n)?.click();
}

function previewSlideImage(input, n) {
  if (!input.files[0]) return;
  const reader = new FileReader();
  reader.onload = e => {
    const container = input.closest('.border-dashed');
    if (!container) return;
    container.style.backgroundImage    = `url(${e.target.result})`;
    container.style.backgroundSize     = 'cover';
    container.style.backgroundPosition = 'center';
    container.innerHTML = `
      <div class="flex items-center gap-2 text-white drop-shadow">
        <i data-lucide="check-circle" class="w-4 h-4"></i>
        <span class="text-xs font-semibold">Image uploaded</span>
      </div>
      <input type="file" id="slideFile${n}" accept="image/*" class="hidden"
        onchange="previewSlideImage(this,${n})" />`;
    lucide.createIcons();
  };
  reader.readAsDataURL(input.files[0]);
}

function saveSlideText(n) {
  const title   = document.getElementById(`slideTitle${n}`)?.value.trim()   || '';
  const caption = document.getElementById(`slideCaption${n}`)?.value.trim() || '';
  // In production, POST to a real API. For now we show a toast.
  console.log(`Slide ${n}:`, { title, caption });
  showCmsToast(`Slide ${n} text saved!`, 'success');
}

function addCarouselSlide() {
  showCmsToast('Add more slides via the backend admin.', 'success');
}

/* ══════════════════════════════════════════════════════════════
   CONTACT SETTINGS
══════════════════════════════════════════════════════════════ */
async function saveContactSettings() {
  const payload = {
    contact_address:  document.getElementById('contactAddress')?.value.trim()  || '',
    contact_phone:    document.getElementById('contactPhone')?.value.trim()    || '',
    contact_email:    document.getElementById('contactEmail')?.value.trim()    || '',
    contact_facebook: document.getElementById('contactFacebook')?.value.trim() || '',
    contact_hours:    document.getElementById('contactHours')?.value.trim()    || '',
  };
  await _postCMS(payload);
}

/* ══════════════════════════════════════════════════════════════
   FOOTER SETTINGS
══════════════════════════════════════════════════════════════ */
async function saveFooterSettings() {
  const payload = {
    footer_tagline:   document.getElementById('footerTagline')?.value.trim()   || '',
    footer_copyright: document.getElementById('footerCopyright')?.value.trim() || '',
  };
  await _postCMS(payload);
}

/* ══════════════════════════════════════════════════════════════
   ABOUT PAGE — PROGRAM CMS  (delegates to program_cms.js globals)
══════════════════════════════════════════════════════════════ */

// ── Program Info ──
async function saveProgramInfo() {
  const data = {
    program_name:         document.getElementById('programName')?.value        || '',
    program_degree:       document.getElementById('programDegree')?.value      || '',
    program_tagline:      document.getElementById('programTagline')?.value     || '',
    program_description:  document.getElementById('programDescription')?.value || '',
    program_institution:  document.getElementById('programInstitution')?.value || '',
    program_copc_number:  document.getElementById('programCOPC')?.value        || '',
    program_effective_year: document.getElementById('programEffectiveYear')?.value || '',
    program_accreditor:   document.getElementById('programAccreditor')?.value  || '',
  };
  try {
    const res  = await fetch('/admin/api/program/cms/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify(data),
    });
    const json = await res.json();
    if (json.success) showCmsToast('Program info saved!', 'success');
    else showCmsToast('Error: ' + json.message, 'error');
  } catch {
    showCmsToast('Network error saving program info.', 'error');
  }
}

// ── Objectives ──
let objectivesData = [];

function loadObjectives(data) {
  objectivesData = data || [];
  const container = document.getElementById('objectivesList');
  if (!container) return;
  container.innerHTML = objectivesData.length ? '' : '<p class="text-sm text-gray-400 text-center py-6">No objectives yet. Click "+ Add Objective" to begin.</p>';
  objectivesData.forEach((obj, idx) => {
    const div = document.createElement('div');
    div.className = 'row-card space-y-2';
    div.innerHTML = `
      <input type="text" placeholder="Objective title" value="${_esc(obj.title)}"
        oninput="objectivesData[${idx}].title = this.value"
        class="field" />
      <textarea placeholder="Description" rows="2"
        oninput="objectivesData[${idx}].description = this.value"
        class="field">${_esc(obj.description)}</textarea>
      <button onclick="removeObjective(${idx})"
        class="text-xs font-semibold text-red-500 hover:text-red-700 flex items-center gap-1">
        <i data-lucide="trash-2" class="w-3 h-3"></i> Remove
      </button>`;
    container.appendChild(div);
  });
  lucide.createIcons();
}

function addObjective() {
  objectivesData.push({ title: '', description: '' });
  loadObjectives(objectivesData);
}

function removeObjective(idx) {
  objectivesData.splice(idx, 1);
  loadObjectives(objectivesData);
}

// ── Outcomes ──
let outcomesData = [];

function loadOutcomes(data) {
  outcomesData = data || [];
  const container = document.getElementById('outcomesList');
  if (!container) return;
  container.innerHTML = outcomesData.length ? '' : '<p class="text-sm text-gray-400 text-center py-6">No outcomes yet. Click "+ Add Outcome" to begin.</p>';
  outcomesData.forEach((out, idx) => {
    const div = document.createElement('div');
    div.className = 'row-card space-y-2';
    div.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <input type="number" min="1" placeholder="No." value="${out.number || idx + 1}"
          oninput="outcomesData[${idx}].number = parseInt(this.value)"
          class="field" style="max-width:80px;" />
        <input type="text" placeholder="Outcome title" value="${_esc(out.title)}"
          oninput="outcomesData[${idx}].title = this.value"
          class="field" />
      </div>
      <textarea placeholder="Description" rows="2"
        oninput="outcomesData[${idx}].description = this.value"
        class="field">${_esc(out.description)}</textarea>
      <button onclick="removeOutcome(${idx})"
        class="text-xs font-semibold text-red-500 hover:text-red-700 flex items-center gap-1">
        <i data-lucide="trash-2" class="w-3 h-3"></i> Remove
      </button>`;
    container.appendChild(div);
  });
  lucide.createIcons();
}

function addOutcome() {
  outcomesData.push({ number: outcomesData.length + 1, title: '', description: '' });
  loadOutcomes(outcomesData);
}

function removeOutcome(idx) {
  outcomesData.splice(idx, 1);
  loadOutcomes(outcomesData);
}

// ── Curriculum ──
let curriculumData = [];

function loadCurriculum(data) {
  curriculumData = data || [];
  const container = document.getElementById('curriculumList');
  if (!container) return;
  container.innerHTML = curriculumData.length ? '' : '<p class="text-sm text-gray-400 text-center py-6">No curriculum groups yet.</p>';
  curriculumData.forEach((group, gIdx) => {
    const coursesHTML = (group.courses || []).map((course, cIdx) => `
      <div class="flex gap-2 mb-2 items-center">
        <input type="text" placeholder="Code" value="${_esc(course.code)}"
          oninput="curriculumData[${gIdx}].courses[${cIdx}].code = this.value"
          class="field" style="width:80px;" />
        <input type="text" placeholder="Course name" value="${_esc(course.name)}"
          oninput="curriculumData[${gIdx}].courses[${cIdx}].name = this.value"
          class="field flex-1" />
        <input type="number" min="1" placeholder="Units" value="${course.units || ''}"
          oninput="curriculumData[${gIdx}].courses[${cIdx}].units = parseInt(this.value)"
          class="field text-center" style="width:64px;" />
        <button onclick="removeCourse(${gIdx}, ${cIdx})" class="btn-del">
          <i data-lucide="x"></i>
        </button>
      </div>`).join('');

    const div = document.createElement('div');
    div.className = 'row-card';
    div.innerHTML = `
      <div class="flex items-center gap-3 mb-3">
        <input type="text" placeholder="Group title (e.g., Core Courses)" value="${_esc(group.title)}"
          oninput="curriculumData[${gIdx}].title = this.value"
          class="field flex-1" />
        <button onclick="removeCurriculumGroup(${gIdx})" class="btn-del"><i data-lucide="trash-2"></i></button>
      </div>
      <div id="courses-group-${gIdx}" class="mb-2">${coursesHTML}</div>
      <button onclick="addCourse(${gIdx})"
        class="text-xs text-red-700 font-semibold hover:text-red-900 flex items-center gap-1">
        <i data-lucide="plus" class="w-3 h-3"></i> Add Course
      </button>`;
    container.appendChild(div);
  });
  lucide.createIcons();
}

function addCurriculumGroup() {
  curriculumData.push({ title: '', courses: [] });
  loadCurriculum(curriculumData);
}

function removeCurriculumGroup(gIdx) {
  curriculumData.splice(gIdx, 1);
  loadCurriculum(curriculumData);
}

function addCourse(gIdx) {
  curriculumData[gIdx].courses = curriculumData[gIdx].courses || [];
  curriculumData[gIdx].courses.push({ code: '', name: '', units: 3 });
  loadCurriculum(curriculumData);
}

function removeCourse(gIdx, cIdx) {
  curriculumData[gIdx].courses.splice(cIdx, 1);
  loadCurriculum(curriculumData);
}

// ── Statistics ──
let statisticsData = [];

function loadStatistics(data) {
  statisticsData = data || [];
  const container = document.getElementById('statisticsList');
  if (!container) return;
  container.innerHTML = statisticsData.length ? '' : '<p class="text-sm text-gray-400 text-center py-6">No statistics yet.</p>';
  statisticsData.forEach((stat, idx) => {
    const div = document.createElement('div');
    div.className = 'row-card flex items-center gap-3';
    div.innerHTML = `
      <input type="text" placeholder="Label (e.g., Graduates)" value="${_esc(stat.stat_label)}"
        oninput="statisticsData[${idx}].stat_label = this.value"
        class="field flex-1" />
      <input type="text" placeholder="Value (e.g., 200+)" value="${_esc(stat.stat_value)}"
        oninput="statisticsData[${idx}].stat_value = this.value"
        class="field flex-1" />
      <button onclick="removeStatistic(${idx})" class="btn-del"><i data-lucide="trash-2"></i></button>`;
    container.appendChild(div);
  });
  lucide.createIcons();
}

function addStatistic() {
  statisticsData.push({ stat_label: '', stat_value: '' });
  loadStatistics(statisticsData);
}

function removeStatistic(idx) {
  statisticsData.splice(idx, 1);
  loadStatistics(statisticsData);
}

// ── Save all program data ──
async function saveProgramCMS() {
  const payload = {
    program_objectives: objectivesData,
    program_outcomes:   outcomesData,
    program_curriculum: curriculumData,
    program_stats:      statisticsData,
  };
  try {
    const res  = await fetch('/admin/api/program/cms/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify(payload),
    });
    const json = await res.json();
    if (json.success) showCmsToast('Program CMS saved!', 'success');
    else showCmsToast('Error: ' + json.message, 'error');
  } catch {
    showCmsToast('Network error.', 'error');
  }
}

/* ══════════════════════════════════════════════════════════════
   PROGRAM CMS — LOAD FROM API
══════════════════════════════════════════════════════════════ */
async function loadProgramCMS() {
  try {
    const res  = await fetch('/admin/api/program/cms/');
    const json = await res.json();
    if (!json.success) return;
    const d = json.data;

    // Populate text fields
    _setVal('programName',          d.program_name);
    _setVal('programDegree',        d.program_degree);
    _setVal('programTagline',       d.program_tagline);
    _setVal('programDescription',   d.program_description);
    _setVal('programInstitution',   d.program_institution);
    _setVal('programCOPC',          d.program_copc_number);
    _setVal('programEffectiveYear', d.program_effective_year);
    _setVal('programAccreditor',    d.program_accreditor);

    // Populate dynamic lists
    loadObjectives(d.program_objectives || []);
    loadOutcomes(d.program_outcomes     || []);
    loadCurriculum(d.program_curriculum || []);
    loadStatistics(d.program_stats      || []);

    // Faculty is loaded lazily on tab open
  } catch (e) {
    console.warn('Could not load program CMS:', e);
  }
}

/* ══════════════════════════════════════════════════════════════
   FACULTY  (Members / Staff tab)
══════════════════════════════════════════════════════════════ */
let facultyData = [];

async function loadFaculty() {
  try {
    const res  = await fetch('/admin/api/faculty/list/');
    const json = await res.json();
    if (!json.success) return;
    facultyData = json.data || [];
    renderFaculty();
  } catch (e) {
    console.warn('Could not load faculty:', e);
  }
}

function renderFaculty() {
  const container = document.getElementById('facultyList');
  if (!container) return;

  if (!facultyData.length) {
    container.innerHTML = `<div class="col-span-3 text-center py-12 text-gray-400 text-sm">
      No faculty members yet. Click "+ Add Member" to begin.
    </div>`;
    return;
  }

  container.innerHTML = facultyData.map(f => {
    const initials = (f.first_name[0] || '') + (f.last_name[0] || '');
    const photo = f.photo
      ? `<img src="${f.photo}" class="w-full h-40 object-cover" alt="${_esc(f.first_name)}" />`
      : `<div class="w-full h-40 bg-gradient-to-br from-red-800 to-red-600 flex items-center justify-center text-white text-2xl font-bold">${initials.toUpperCase()}</div>`;
    return `
      <div class="rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition">
        ${photo}
        <div class="p-4">
          <p class="font-bold text-gray-800 text-sm">${_esc(f.first_name)} ${_esc(f.last_name)}</p>
          <p class="text-xs text-gray-500 mt-0.5">${_esc(f.title)}</p>
          <p class="text-xs text-gray-400 mt-2 line-clamp-2">${_esc(f.specializations)}</p>
          <div class="flex gap-2 mt-3">
            <button onclick="openEditFacultyModal(${f.id})"
              class="flex-1 py-1.5 border border-blue-200 rounded-lg text-xs font-semibold text-blue-600 hover:bg-blue-50">
              Edit
            </button>
            <button onclick="deleteFaculty(${f.id})"
              class="flex-1 py-1.5 border border-red-200 rounded-lg text-xs font-semibold text-red-600 hover:bg-red-50">
              Delete
            </button>
          </div>
        </div>
      </div>`;
  }).join('');
  lucide.createIcons();
}

function openAddFacultyModal() {
  document.getElementById('facultyModalTitle').textContent = 'Add Faculty Member';
  document.getElementById('facultyFirstName').value        = '';
  document.getElementById('facultyLastName').value         = '';
  document.getElementById('facultyTitle').value            = '';
  document.getElementById('facultySpecializations').value  = '';
  document.getElementById('facultyPhoto').value            = '';
  document.getElementById('facultyModal')._editId          = null;
  document.getElementById('facultyModal').style.display    = 'flex';
  lucide.createIcons();
}

function openEditFacultyModal(id) {
  const f = facultyData.find(x => x.id === id);
  if (!f) return;
  document.getElementById('facultyModalTitle').textContent = 'Edit Faculty Member';
  document.getElementById('facultyFirstName').value        = f.first_name;
  document.getElementById('facultyLastName').value         = f.last_name;
  document.getElementById('facultyTitle').value            = f.title;
  document.getElementById('facultySpecializations').value  = f.specializations;
  document.getElementById('facultyModal')._editId          = id;
  document.getElementById('facultyModal').style.display    = 'flex';
  lucide.createIcons();
}

function closeFacultyModal() {
  document.getElementById('facultyModal').style.display = 'none';
}

async function saveFacultyMember() {
  const firstName       = document.getElementById('facultyFirstName').value.trim();
  const lastName        = document.getElementById('facultyLastName').value.trim();
  const title           = document.getElementById('facultyTitle').value.trim();
  const specializations = document.getElementById('facultySpecializations').value.trim();
  const photoFile       = document.getElementById('facultyPhoto').files[0];
  const editId          = document.getElementById('facultyModal')._editId;

  if (!firstName || !lastName || !title) {
    showCmsToast('First name, last name and title are required.', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('first_name',       firstName);
  formData.append('last_name',        lastName);
  formData.append('title',            title);
  formData.append('specializations',  specializations);
  if (photoFile) formData.append('photo', photoFile);
  if (editId)    formData.append('faculty_id', editId);

  const url = editId ? '/admin/api/faculty/update/' : '/admin/api/faculty/add/';

  try {
    const res  = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCSRFToken() },
      body: formData,
    });
    const json = await res.json();
    if (json.success) {
      showCmsToast(editId ? 'Member updated!' : 'Member added!', 'success');
      closeFacultyModal();
      await loadFaculty();
    } else {
      showCmsToast('Error: ' + json.message, 'error');
    }
  } catch {
    showCmsToast('Network error.', 'error');
  }
}

async function deleteFaculty(id) {
  if (!confirm('Delete this faculty member?')) return;
  try {
    const res  = await fetch('/admin/api/faculty/delete/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
      body: JSON.stringify({ faculty_id: id }),
    });
    const json = await res.json();
    if (json.success) {
      showCmsToast('Member deleted.', 'success');
      await loadFaculty();
    } else {
      showCmsToast('Error: ' + json.message, 'error');
    }
  } catch {
    showCmsToast('Network error.', 'error');
  }
}

/* ══════════════════════════════════════════════════════════════
   ACCOUNT MANAGEMENT  (placeholder — extend as needed)
══════════════════════════════════════════════════════════════ */
function initAccountManagement() {
  // Future: fetch /admin/api/users/ and populate #usersTableBody
}

/* ══════════════════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════════════════ */
function _esc(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function _setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val || '';
}

/* ══════════════════════════════════════════════════════════════
   MODAL BACKDROP CLOSE
══════════════════════════════════════════════════════════════ */
function _initModalBackdrops() {
  const facultyModal = document.getElementById('facultyModal');
  if (facultyModal) {
    facultyModal.addEventListener('click', e => {
      if (e.target === facultyModal) closeFacultyModal();
    });
  }
}

/* ══════════════════════════════════════════════════════════════
   HISTORY LOGS TAB
══════════════════════════════════════════════════════════════ */
function renderHistoryLogs(activities) {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;
  if (!activities || !activities.length) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-400 py-8 text-sm">No activity history yet.</td></tr>';
    return;
  }
  tbody.innerHTML = activities.map(act => `
    <tr>
      <td>
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold
          ${act.action === 'verified'   ? 'bg-green-50 text-green-700'  :
            act.action === 'rejected'   ? 'bg-red-50 text-red-700'      :
            act.action === 'cms_updated'? 'bg-blue-50 text-blue-700'    :
                                          'bg-gray-100 text-gray-600'}">
          ${_esc(act.action_display || act.action)}
        </span>
      </td>
      <td class="font-medium text-gray-800">${_esc(act.admin || '—')}</td>
      <td class="text-gray-500 text-xs">${_esc(act.application_id || act.notes || '—')}</td>
      <td class="text-gray-400 text-xs whitespace-nowrap">${_esc(act.timestamp || '')}</td>
    </tr>`).join('');
}

/* ══════════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  _initDownloadsUpload();
  _initModalBackdrops();

  // ── Render history logs if data was injected by Django ──
  // The template should inject:  <script>window.CMS_ACTIVITIES = {{ all_activities|safe }};</script>
  if (typeof window.CMS_ACTIVITIES !== 'undefined') {
    renderHistoryLogs(window.CMS_ACTIVITIES);
  }

  // ── Load program CMS data for the About Page tab ──
  loadProgramCMS();

  // ── The HTML already has active classes set correctly on default tabs ──
  // No JS tab-switching needed on init — CSS classes in the HTML handle it.
  lucide.createIcons();
});