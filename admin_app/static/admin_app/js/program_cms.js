// Program CMS Management JavaScript

let programCMSData = {};
let objectivesData = [];
let outcomesData = [];
let curriculumData = [];
let statisticsData = [];
let facultyData = [];

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
        document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1] || '';
}

// Load program CMS data
async function loadProgramCMS() {
    try {
        const response = await fetch('/admin-panel/api/program/cms/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        const data = await response.json();
        
        if (data.success) {
            populateProgramInfo(data.data);
        }
    } catch (error) {
        console.error('Error loading program CMS:', error);
    }
}

// Switch tabs in program section
function switchProgramTab(tabName, button) {
  // Hide all tabs
  document.querySelectorAll('.program-tab-content').forEach(tab => {
    tab.classList.add('hidden');
  });
  
  // Remove active state from all buttons
  document.querySelectorAll('.program-tab').forEach(btn => {
    btn.classList.remove('active', 'border-b-2', 'border-red-800', 'text-red-800');
    btn.classList.add('border-transparent', 'text-gray-500');
  });
  
  // Show selected tab
  const tabElement = document.getElementById(`program-tab-${tabName}`);
  if (tabElement) {
    tabElement.classList.remove('hidden');
  }
  
  // Activate button
  button.classList.remove('border-transparent', 'text-gray-500');
  button.classList.add('active', 'border-b-2', 'border-red-800', 'text-red-800');
}

// Populate program info forms
function populateProgramInfo(data) {
    // Fill in the program info fields if they exist
    const fields = ['program_name', 'program_degree', 'program_title', 'program_tagline', 
                    'program_description', 'program_institution', 'program_copc_number', 
                    'program_effective_year', 'program_accreditor'];
    
    fields.forEach(field => {
        const element = document.getElementById(field);
        if (element && data[field]) {
            element.value = data[field];
        }
    });
}

// Save program basic info
async function saveProgramInfo() {
  const data = {
    program_name: document.getElementById('programName').value,
    program_degree: document.getElementById('programDegree').value,
    program_tagline: document.getElementById('programTagline').value,
    program_description: document.getElementById('programDescription').value,
    program_institution: document.getElementById('programInstitution').value,
    program_copc_number: document.getElementById('programCOPC').value,
    program_effective_year: document.getElementById('programEffectiveYear').value,
    program_accreditor: document.getElementById('programAccreditor').value,
  };

  try {
    const response = await fetch('/admin/api/program/cms/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    if (result.success) {
      showToast('Program info saved successfully', 'success');
    } else {
      showToast('Error: ' + result.message, 'error');
    }
  } catch (e) {
    showToast('Error saving program info', 'error');
  }
}

// Objectives management
function loadObjectives() {
  objectivesData = programCMSData.program_objectives || [];
  const container = document.getElementById('objectivesList');
  container.innerHTML = '';
  
  objectivesData.forEach((obj, idx) => {
    const html = `
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <input type="text" placeholder="Objective title" value="${obj.title}" 
          onchange="objectivesData[${idx}].title = this.value" 
          class="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:outline-none focus:ring-2 focus:ring-red-800">
        <textarea placeholder="Description" rows="2" 
          onchange="objectivesData[${idx}].description = this.value"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">${obj.description}</textarea>
        <button onclick="removeObjective(${idx})" class="mt-2 text-sm text-red-600 hover:text-red-800 font-medium">Delete</button>
      </div>
    `;
    container.innerHTML += html;
  });
}

function addObjective() {
  objectivesData.push({ title: '', description: '' });
  loadObjectives();
}

function removeObjective(idx) {
  objectivesData.splice(idx, 1);
  loadObjectives();
}

// Outcomes management
function loadOutcomes() {
  outcomesData = programCMSData.program_outcomes || [];
  const container = document.getElementById('outcomesList');
  container.innerHTML = '';
  
  outcomesData.forEach((out, idx) => {
    const html = `
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-2">
          <input type="number" min="1" placeholder="Number" value="${out.number}" 
            onchange="outcomesData[${idx}].number = parseInt(this.value)" 
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
          <input type="text" placeholder="Outcome title" value="${out.title}" 
            onchange="outcomesData[${idx}].title = this.value" 
            class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
        </div>
        <textarea placeholder="Description" rows="2" 
          onchange="outcomesData[${idx}].description = this.value"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">${out.description}</textarea>
        <button onclick="removeOutcome(${idx})" class="mt-2 text-sm text-red-600 hover:text-red-800 font-medium">Delete</button>
      </div>
    `;
    container.innerHTML += html;
  });
}

function addOutcome() {
  outcomesData.push({ number: outcomesData.length + 1, title: '', description: '' });
  loadOutcomes();
}

function removeOutcome(idx) {
  outcomesData.splice(idx, 1);
  loadOutcomes();
}

// Curriculum management
function loadCurriculum() {
  curriculumData = programCMSData.program_curriculum || [];
  const container = document.getElementById('curriculumList');
  container.innerHTML = '';
  
  curriculumData.forEach((group, gIdx) => {
    const coursesHtml = (group.courses || []).map((course, cIdx) => `
      <div class="flex gap-2 mb-2">
        <input type="text" placeholder="Code" value="${course.code}" 
          onchange="curriculumData[${gIdx}].courses[${cIdx}].code = this.value" 
          class="w-20 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-red-800">
        <input type="text" placeholder="Course name" value="${course.name}" 
          onchange="curriculumData[${gIdx}].courses[${cIdx}].name = this.value" 
          class="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-red-800">
        <input type="number" min="1" placeholder="Units" value="${course.units}" 
          onchange="curriculumData[${gIdx}].courses[${cIdx}].units = parseInt(this.value)" 
          class="w-16 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-red-800">
        <button onclick="removeCourse(${gIdx}, ${cIdx})" class="text-red-600 hover:text-red-800 font-medium">✕</button>
      </div>
    `).join('');
    
    const html = `
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div class="flex items-center justify-between mb-3">
          <input type="text" placeholder="Group title (e.g., Core Courses)" value="${group.title}" 
            onchange="curriculumData[${gIdx}].title = this.value" 
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
          <button onclick="removeCurriculumGroup(${gIdx})" class="ml-2 text-red-600 hover:text-red-800 font-medium">Delete Group</button>
        </div>
        <div class="pl-2">${coursesHtml}</div>
        <button onclick="addCourse(${gIdx})" class="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium">+ Add Course</button>
      </div>
    `;
    container.innerHTML += html;
  });
}

function addCurriculumGroup() {
  curriculumData.push({ title: '', courses: [] });
  loadCurriculum();
}

function addCourse(groupIdx) {
  curriculumData[groupIdx].courses.push({ code: '', name: '', units: 3 });
  loadCurriculum();
}

function removeCourse(groupIdx, courseIdx) {
  curriculumData[groupIdx].courses.splice(courseIdx, 1);
  loadCurriculum();
}

function removeCurriculumGroup(idx) {
  curriculumData.splice(idx, 1);
  loadCurriculum();
}

// Statistics management
function loadStatistics() {
  statisticsData = programCMSData.program_stats || [];
  const container = document.getElementById('statisticsList');
  container.innerHTML = '';
  
  statisticsData.forEach((stat, idx) => {
    const html = `
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 flex gap-3">
        <input type="text" placeholder="Label" value="${stat.stat_label}" 
          onchange="statisticsData[${idx}].stat_label = this.value" 
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
        <input type="text" placeholder="Value" value="${stat.stat_value}" 
          onchange="statisticsData[${idx}].stat_value = this.value" 
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
        <button onclick="removeStatistic(${idx})" class="text-red-600 hover:text-red-800 font-medium">Delete</button>
      </div>
    `;
    container.innerHTML += html;
  });
}

function addStatistic() {
  statisticsData.push({ stat_label: '', stat_value: '' });
  loadStatistics();
}

function removeStatistic(idx) {
  statisticsData.splice(idx, 1);
  loadStatistics();
}

// Faculty management
function loadFaculty() {
  facultyData = programCMSData.faculties || [];
  const container = document.getElementById('facultyList');
  container.innerHTML = '';
  
  facultyData.forEach((faculty) => {
    const html = `
      <div class="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
        ${faculty.photo ? `<img src="${faculty.photo}" class="w-full h-40 object-cover">` : `<div class="w-full h-40 bg-gradient-to-br from-red-800 to-red-600 flex items-center justify-center text-white text-2xl font-bold">${faculty.first_name[0]}${faculty.last_name[0]}</div>`}
        <div class="p-4">
          <h3 class="font-semibold text-gray-800">${faculty.first_name} ${faculty.last_name}</h3>
          <p class="text-sm text-gray-600">${faculty.title}</p>
          <p class="text-xs text-gray-500 mt-2">${faculty.specializations}</p>
          <div class="flex gap-2 mt-3">
            <button onclick="editFaculty(${faculty.id})" class="flex-1 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Edit</button>
            <button onclick="deleteFaculty(${faculty.id})" class="flex-1 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">Delete</button>
          </div>
        </div>
      </div>
    `;
    container.innerHTML += html;
  });
}

function openAddFacultyModal() {
  // Create modal HTML
  const html = `
    <div id="facultyModal" class="modal-overlay">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl">
        <div class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 class="text-xl font-bold text-gray-800">Add Faculty Member</h2>
          <button onclick="closeFacultyModal()" class="text-gray-400 hover:text-gray-600">
            <i data-lucide="x" class="w-6 h-6"></i>
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" id="facultyFirstName" placeholder="First Name" 
              class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
            <input type="text" id="facultyLastName" placeholder="Last Name" 
              class="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
          </div>
          <input type="text" id="facultyTitle" placeholder="Title (e.g., Associate Professor)" 
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
          <textarea id="facultySpecializations" placeholder="Specializations (comma-separated)" rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800"></textarea>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Photo (optional)</label>
            <input type="file" id="facultyPhoto" accept="image/*" 
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-800">
          </div>
        </div>
        <div class="p-6 pt-0 flex gap-3">
          <button onclick="closeFacultyModal()" class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onclick="saveFacultyMember()" class="flex-1 px-4 py-2.5 bg-red-800 text-white rounded-xl text-sm font-semibold hover:bg-red-900">Save Faculty</button>
        </div>
      </div>
    </div>
  `;
  
  // Create modal element
  const modalDiv = document.createElement('div');
  modalDiv.innerHTML = html;
  document.body.appendChild(modalDiv.firstElementChild);
  document.getElementById('facultyModal').style.display = 'flex';
  lucide.createIcons();
}

function closeFacultyModal() {
  const modal = document.getElementById('facultyModal');
  if (modal) modal.remove();
}

async function saveFacultyMember() {
  const firstName = document.getElementById('facultyFirstName').value;
  const lastName = document.getElementById('facultyLastName').value;
  const title = document.getElementById('facultyTitle').value;
  const specializations = document.getElementById('facultySpecializations').value;
  const photoFile = document.getElementById('facultyPhoto').files[0];

  if (!firstName || !lastName || !title) {
    showToast('Please fill in all required fields', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('first_name', firstName);
  formData.append('last_name', lastName);
  formData.append('title', title);
  formData.append('specializations', specializations);
  if (photoFile) formData.append('photo', photoFile);

  try {
    const response = await fetch('/admin/api/faculty/add/', {
      method: 'POST',
      body: formData
    });
    const result = await response.json();
    if (result.success) {
      showToast('Faculty member added', 'success');
      closeFacultyModal();
      loadFaculty();
    } else {
      showToast('Error: ' + result.message, 'error');
    }
  } catch (e) {
    showToast('Error adding faculty member', 'error');
  }
}

async function editFaculty(facultyId) {
  const faculty = facultyData.find(f => f.id === facultyId);
  if (!faculty) return;

  // Similar to add modal but with edit functionality
  showToast('Edit faculty functionality coming soon', 'info');
}

async function deleteFaculty(facultyId) {
  if (!confirm('Delete this faculty member?')) return;

  try {
    const response = await fetch('/admin/api/faculty/delete/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ faculty_id: facultyId })
    });
    const result = await response.json();
    if (result.success) {
      showToast('Faculty member deleted', 'success');
      loadFaculty();
    } else {
      showToast('Error: ' + result.message, 'error');
    }
  } catch (e) {
    showToast('Error deleting faculty member', 'error');
  }
}

// Save all program data
async function saveProgramCMS() {
  const data = {
    program_objectives: objectivesData,
    program_outcomes: outcomesData,
    program_curriculum: curriculumData,
    program_stats: statisticsData
  };

  try {
    const response = await fetch('/admin/api/program/cms/update/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    if (result.success) {
      showToast('Program CMS updated successfully', 'success');
    } else {
      showToast('Error: ' + result.message, 'error');
    }
  } catch (e) {
    showToast('Error saving program CMS', 'error');
  }
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', loadProgramCMS);
