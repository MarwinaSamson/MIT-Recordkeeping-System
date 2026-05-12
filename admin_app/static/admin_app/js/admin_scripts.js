lucide.createIcons();

// Dynamic data from Django context - initialized from contextData
let applications = [];
let activityLog = [];
let toastTimer;  // Timer for toast notifications
let selectedApp;  // Currently selected application in modal
let rejectTargetIdx;  // Index of document being rejected

// Initialize data from contextData when page loads
function initializeData() {
  if(typeof contextData !== 'undefined') {
    applications = contextData.allApplications || [];
    activityLog = contextData.allActivities || [];
    console.log('Data initialized. Applications count:', applications.length);
    console.log('Applications data:', applications);
  } else {
    console.warn('contextData is not defined!');
  }
}

// Prospectus management client-side store (temporary, will be replaced by API)
let prospectuses = [];

function renderProspectusPage(){
  const container = document.getElementById('prospectusList');
  if(!container) return;
  // Load prospectuses from backend
  fetch('/admin-panel/api/prospectuses/', { method: 'GET', headers: {'Accept':'application/json'}, credentials: 'same-origin' })
    .then(r=>r.json())
    .then(res=>{
      if(!res.success){ container.innerHTML = `<div class="text-gray-400 text-sm">Error loading prospectuses.</div>`; return; }
      prospectuses = res.data || [];
      if(!prospectuses.length){ container.innerHTML = `<div class="text-gray-400 text-sm">No prospectuses created yet.</div>`; return; }
      container.innerHTML = prospectuses.map((p,idx)=>{
        return `
      <div class="p-3 border rounded-lg flex items-start justify-between">
        <div>
          <div class="font-semibold text-gray-800">${escapeHtml(p.name)}</div>
          <div class="text-xs text-gray-500 mt-1">${escapeHtml(p.description||'')}</div>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn btn-outline btn-sm" onclick="deleteProspectus(${p.id})">Delete</button>
        </div>
      </div>`;
      }).join('');
    })
    .catch(err=>{ console.error('Error fetching prospectuses',err); container.innerHTML = `<div class="text-gray-400 text-sm">Error loading prospectuses.</div>`; });
}

// Prospectus builder state
let currentBuilder = { name: '', description: '', years: [] };

function resetBuilder(){
  currentBuilder = { name: '', description: '', years: [] };
  const nameEl = document.getElementById('builderName');
  const descEl = document.getElementById('builderDesc');
  if(nameEl) nameEl.value='';
  if(descEl) descEl.value='';
  renderBuilder();
}

function addYear(){
  const yearIdx = currentBuilder.years.length;
  currentBuilder.years.push({ label: `Year ${yearIdx+1}`, semesters: [ { label: 'First Semester', subjects: [] } ] });
  renderBuilder();
}

function removeYear(yIdx){
  if(!confirm('Remove this year and all its semesters?')) return;
  currentBuilder.years.splice(yIdx,1);
  renderBuilder();
}

function addSemester(yIdx){
  currentBuilder.years[yIdx].semesters.push({ label: 'New Semester', subjects: [] });
  renderBuilder();
}

function removeSemester(yIdx,sIdx){
  if(!confirm('Remove this semester and its subjects?')) return;
  currentBuilder.years[yIdx].semesters.splice(sIdx,1);
  renderBuilder();
}

function addSubject(yIdx,sIdx){
  currentBuilder.years[yIdx].semesters[sIdx].subjects.push({ code:'', title:'', prereq:'', lec:3, lab:0, total:3 });
  renderBuilder();
}

function removeSubject(yIdx,sIdx,subIdx){
  currentBuilder.years[yIdx].semesters[sIdx].subjects.splice(subIdx,1);
  renderBuilder();
}

function updateYearLabel(yIdx,val){ currentBuilder.years[yIdx].label = val; }
function updateSemesterLabel(yIdx,sIdx,val){ currentBuilder.years[yIdx].semesters[sIdx].label = val; }
function updateSubjectField(yIdx,sIdx,subIdx,field,val){ currentBuilder.years[yIdx].semesters[sIdx].subjects[subIdx][field] = val; }

function renderBuilder(){
  const container = document.getElementById('builderYears');
  if(!container) return;
  if(!currentBuilder.years.length){ container.innerHTML = `<div class="text-gray-400 text-sm">No years yet. Click "Add Year" to start.</div>`; return; }
  container.innerHTML = currentBuilder.years.map((y,yIdx)=>{
    return `
      <div class="p-3 border rounded-lg">
        <div class="flex items-center justify-between mb-2">
          <input value="${escapeHtml(y.label)}" oninput="updateYearLabel(${yIdx}, this.value)" class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-700 text-sm" />
          <div class="flex items-center gap-2">
            <button class="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50" onclick="addSemester(${yIdx})" type="button">Add Semester</button>
            <button class="px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg" onclick="removeYear(${yIdx})" type="button">Delete Year</button>
          </div>
        </div>
        <div class="space-y-3">
          ${y.semesters.map((s,sIdx)=>`
                <div class="p-3 border rounded-lg bg-gray-50">
              <div class="flex items-center justify-between mb-2">
                <input value="${escapeHtml(s.label)}" oninput="updateSemesterLabel(${yIdx}, ${sIdx}, this.value)" class="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-700 text-sm" />
                <div class="flex items-center gap-2">
                  <button class="px-2 py-1 border border-gray-300 rounded-lg text-sm hover:bg-gray-50" onclick="addSubject(${yIdx}, ${sIdx})" type="button">Add Subject</button>
                  <button class="px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg" onclick="removeSemester(${yIdx}, ${sIdx})" type="button">Delete Semester</button>
                </div>
              </div>
              <div class="space-y-2">
                <div class="grid grid-cols-12 gap-2 items-center bg-white p-2 rounded-md border border-gray-100 text-xs text-gray-500 font-semibold">
                  <div class="col-span-2">CODE</div>
                  <div class="col-span-5">DESCRIPTIVE TITLE</div>
                  <div class="col-span-2">PREREQ</div>
                  <div class="col-span-1 text-center">LEC</div>
                  <div class="col-span-1 text-center">LAB</div>
                  <div class="col-span-1 text-center">TOTAL</div>
                  <div class="col-span-1 text-right">GRADE</div>
                </div>
                ${s.subjects.map((sub,subIdx)=>`
                  <div class="grid grid-cols-12 gap-2 items-center bg-white p-2 rounded-md border border-gray-50">
                    <div class="col-span-2"><input value="${escapeHtml(sub.code)}" placeholder="Code" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'code',this.value)" class="w-full px-3 py-2 border border-gray-200 rounded text-sm"/></div>
                    <div class="col-span-5"><input value="${escapeHtml(sub.title)}" placeholder="Descriptive Title" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'title',this.value)" class="w-full px-3 py-2 border border-gray-200 rounded text-sm"/></div>
                    <div class="col-span-2"><input value="${escapeHtml(sub.prereq)}" placeholder="Prereq" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'prereq',this.value)" class="w-full px-3 py-2 border border-gray-200 rounded text-sm"/></div>
                    <div class="col-span-1"><input type="number" value="${sub.lec}" min="0" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'lec',this.value);renderBuilder()" class="w-full px-3 py-2 border border-gray-200 rounded text-sm text-center"/></div>
                    <div class="col-span-1"><input type="number" value="${sub.lab}" min="0" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'lab',this.value);renderBuilder()" class="w-full px-3 py-2 border border-gray-200 rounded text-sm text-center"/></div>
                    <div class="col-span-1"><input type="number" value="${sub.total}" min="0" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'total',this.value);renderBuilder()" class="w-full px-3 py-2 border border-gray-200 rounded text-sm text-center"/></div>
                    <div class="col-span-1 text-right"><input value="${escapeHtml(sub.grade||'--')}" placeholder="--" oninput="updateSubjectField(${yIdx},${sIdx},${subIdx},'grade',this.value)" class="w-20 px-2 py-1 border border-gray-200 rounded text-sm text-center" /></div>
                  </div>
                `).join('')}
                <div class="grid grid-cols-12 gap-2 items-center mt-2 p-2 bg-gray-50 rounded-md border border-gray-100 text-sm font-semibold">
                  <div class="col-span-9 text-right">TOTAL</div>
                  <div class="col-span-1 text-center">${s.subjects.reduce((a,b)=>a+Number(b.lec||0),0)}</div>
                  <div class="col-span-1 text-center">${s.subjects.reduce((a,b)=>a+Number(b.lab||0),0)}</div>
                  <div class="col-span-1 text-center">${s.subjects.reduce((a,b)=>a+Number(b.total||0),0)}</div>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

function saveBuilderAsProspectus(){
  const name = document.getElementById('builderName').value.trim();
  const desc = document.getElementById('builderDesc').value.trim();
  if(!name){ showToast('Prospectus name required','error'); return; }
  const programSelect = document.getElementById('builderProgramSelect');
  const program_name = programSelect?.value || '';
  const payload = { name, description: desc, years: currentBuilder.years, program_name };
  fetch('/admin-panel/api/prospectuses/create/', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type':'application/json','X-CSRFToken': getCSRFToken()},
    body: JSON.stringify(payload)
  }).then(r=>r.json()).then(res=>{
    if(res.success){ showToast('Prospectus saved'); resetBuilder(); renderProspectusPage(); }
    else showToast(res.message||'Unable to save', 'error');
  }).catch(err=>{ console.error(err); showToast('Network error', 'error'); });
}

// small helper to escape HTML for values
function escapeHtml(s){ if(!s) return ''; return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'); }

function deleteProspectus(id){
  if(!confirm('Delete this prospectus?')) return;
  fetch(`/admin-panel/api/prospectuses/${id}/delete/`, {
    method: 'POST',
    credentials: 'same-origin',
    headers: {'Content-Type':'application/json','X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({id})
  }).then(r=>r.json()).then(res=>{
    if(res.success){ showToast('Prospectus deleted'); renderProspectusPage(); }
    else showToast(res.message||'Unable to delete','error');
  }).catch(err=>{ console.error(err); showToast('Network error','error'); });
}

// Prospectus modal controls
function openProspectusModal(){
  resetBuilder();
  renderBuilder();
  // populate programs select from backend
  fetch('/admin-panel/api/programs/', { credentials: 'same-origin' }).then(r=>r.json()).then(res=>{
    const sel = document.getElementById('builderProgramSelect');
    if(!sel) return;
    sel.innerHTML = '<option value="">Select program</option>';
    if(res && res.success && Array.isArray(res.data)){
      res.data.forEach(p=>{
        const opt = document.createElement('option'); opt.value = p.name; opt.textContent = p.program_label || p.name; sel.appendChild(opt);
      });
    }
  }).catch(err=>{ console.warn('Failed to load programs',err); });

  const modal = document.getElementById('prospectusModal');
  if(modal){ modal.classList.add('open'); modal.style.display='flex'; }
}
function closeProspectusModal(){
  const modal = document.getElementById('prospectusModal');
  if(modal){ modal.classList.remove('open'); modal.style.display='none'; }
}
document.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ closeProspectusModal(); } });
document.getElementById('prospectusModal')?.addEventListener('click', function(e){ if(e.target===this) closeProspectusModal(); });

// Initialize on page load
// Populate Admission Details (School Year, Semester, Curriculum)
function populateAdmissionDetails(){
  const semEl = document.getElementById('admSemester');
  const yearEl = document.getElementById('admYear');
  const levelEl = document.getElementById('admProgramLevel');
  const currEl = document.getElementById('admCurriculum');
  let activeSchoolYearName = '';
  let activeSemesterName = '';
  
  // Determine which values to try to set (from selectedApp or empty)
  const targetCurriculum = window.selectedApp?.student_curriculum || window.selectedApp?.curriculum || '';
  const targetSemester = window.selectedApp?.semester || '';
  const targetYear = window.selectedApp?.year_admitted || '';
  const targetProgramLevel = window.selectedApp?.program_level || '';
  const userId = window.selectedApp?.user_id || null;
  
  // Load all options in parallel
  Promise.all([
    // Load semesters
    fetch('/admin-panel/api/admission/semesters/', { 
      method: 'GET', 
      credentials: 'same-origin', 
      headers: {'Accept':'application/json'} 
    })
      .then(r=>r.json())
      .then(res=>{
        if(!semEl) return;
        semEl.innerHTML = '<option value="">— Select —</option>';
        if(res && res.success && Array.isArray(res.semesters) && res.semesters.length){
          res.semesters.forEach(s=>{ 
            const opt=document.createElement('option'); 
            opt.value=s.name || ''; 
            opt.textContent=s.name || ''; 
            semEl.appendChild(opt); 
          });
        } else {
          ['1st Semester','2nd Semester','Summer'].forEach(s=>{ 
            const opt=document.createElement('option'); 
            opt.value=s; 
            opt.textContent=s; 
            semEl.appendChild(opt); 
          });
        }
        return 'semesters';
      })
      .catch(err=>{ console.warn('Failed to load semesters', err); }),
      
    // Load school years and get active one (with active semester)
    fetch('/admin-panel/api/admission/active-school-year/', { 
      method: 'GET', 
      credentials: 'same-origin', 
      headers: {'Accept':'application/json'} 
    })
      .then(r=>r.json())
      .then(res=>{
        if(res && res.success && res.data){
          activeSchoolYearName = res.data.school_year?.name || '';
          activeSemesterName = res.data.active_semester?.name || '';
        }
        return 'active_schoolyear';
      })
      .catch(err=>{ console.warn('Failed to load active school year', err); }),
      
    // Load all school years
    fetch('/admin-panel/api/admission/school-years/', { 
      method: 'GET', 
      credentials: 'same-origin', 
      headers: {'Accept':'application/json'} 
    })
      .then(r=>r.json())
      .then(res=>{
        if(!yearEl) return;
        yearEl.innerHTML = '<option value="">— Select —</option>';
        if(res && res.success && Array.isArray(res.school_years) && res.school_years.length){
          res.school_years.forEach(y=>{ 
            const opt=document.createElement('option'); 
            opt.value=y.name; 
            opt.textContent=y.name; 
            yearEl.appendChild(opt); 
          });
        }
        return 'schoolyears';
      })
      .catch(err=>{ console.warn('Failed to load school years', err); }),
      
    // Load program levels from Program table
    fetch('/admin-panel/api/programs/', {
      method: 'GET',
      credentials: 'same-origin',
      headers: {'Accept':'application/json'}
    })
      .then(r=>r.json())
      .then(res=>{
        if(!levelEl) return;
        levelEl.innerHTML = '<option value="">— Select Level —</option>';
        if(res && res.success && Array.isArray(res.data) && res.data.length){
          res.data.forEach(program=>{
            const opt=document.createElement('option');
            opt.value=program.name;
            opt.textContent=program.program_label || program.name;
            levelEl.appendChild(opt);
          });
        }
      })
      .catch(err=>{ console.warn('Failed to load programs', err); }),
      
    // Load curricula
    fetch('/admin-panel/api/admission/curricula/', { 
      method: 'GET', 
      credentials: 'same-origin', 
      headers: {'Accept':'application/json'} 
    })
      .then(r=>r.json())
      .then(res=>{
        if(!currEl) return;
        currEl.innerHTML = '<option value="">— Select Curriculum —</option>';
        if(res && res.success && Array.isArray(res.curricula) && res.curricula.length){
          res.curricula.forEach(c=>{ 
            const opt=document.createElement('option'); 
            opt.value=c.name; 
            opt.textContent=c.name + (c.program_name ? ' — '+c.program_name : ''); 
            currEl.appendChild(opt); 
          });
        }
        return 'curricula';
      })
      .catch(err=>{ console.warn('Failed to load curricula', err); })
  ]).then(() => {
    // After all options are loaded, set the values
    
    // Set semester from app data if present, otherwise use the active semester from DB
    if(semEl){
      semEl.value = targetSemester || activeSemesterName || '';
    }
    
    // Set school year from app data if present, otherwise use the active school year from DB
    if(yearEl){
      yearEl.value = targetYear || activeSchoolYearName || '';
    }
    
    // Set curriculum - fetch from student's EducationalBackground (graduate level)
    if(currEl && userId){
      fetch(`/admin-panel/api/admission/student-curriculum/${userId}/`, { 
        method: 'GET', 
        credentials: 'same-origin', 
        headers: {'Accept':'application/json'} 
      })
        .then(r=>r.json())
        .then(res=>{
          // Use student's curriculum if found and no app override
          if(res.success && res.curriculum && !targetCurriculum){
            currEl.value = res.curriculum;
          } else if(targetCurriculum){
            // Use app stored curriculum as fallback
            currEl.value = targetCurriculum;
          }
        })
        .catch(err=>{ 
          // Fallback to application's stored curriculum
          if(targetCurriculum && currEl){
            currEl.value = targetCurriculum;
          }
        });
    } else if(currEl && targetCurriculum){
      currEl.value = targetCurriculum;
    }
  }).catch(err=>{ console.warn('Error in populateAdmissionDetails', err); });
}

if(document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeData);
} else {
  initializeData();
}

// Assignment UI removed — creation-time program selection is used instead.

function assignProspectus(){
  const pSelect = document.getElementById('assignProspectusSelect');
  const progSelect = document.getElementById('assignProgramSelect');
  const progCode = document.getElementById('assignProgramCode');
  const intake = document.getElementById('assignIntakeYear');
  const prospectus_id = pSelect?.value;
  const program_name = (progSelect?.value || '').trim();
  const program_code = (progCode?.value || '').trim();
  const intake_year = (intake?.value || '').trim();
  if(!prospectus_id){ showToast('Select a prospectus to assign','error'); return; }
  if(!program_name && !program_code){ if(!confirm('Assigning without a program name or code. Continue?') ) return; }
  const payload = { prospectus_id: Number(prospectus_id), program_name, program_code, intake_year };
  fetch('/admin-panel/api/prospectuses/assign/', { method: 'POST', headers: {'Content-Type':'application/json','X-CSRFToken': getCSRFToken()}, body: JSON.stringify(payload) })
    .then(r=>r.json()).then(res=>{
      if(res.success){ showToast('Assigned prospectus'); }
      else showToast(res.message||'Unable to assign','error');
    }).catch(err=>{ console.error(err); showToast('Network error','error'); });
}

// Document status summary function
function getDocStatus(docs){
  const v = docs.filter(d => d.status === "Verified").length;
  const p = docs.filter(d => d.status === "Pending Review" || d.status === "Under Review").length;
  const r = docs.filter(d => d.status === "Rejected").length;
  const m = docs.filter(d => d.missing === true || d.status === "Missing").length;
  let h = "";
  if(v) h += `<span class="flex items-center gap-1"><span class="dot dot-green"></span>${v} Verified</span>`;
  if(p) h += `<span class="flex items-center gap-1"><span class="dot dot-orange"></span>${p} Pending</span>`;
  if(r) h += `<span class="flex items-center gap-1"><span class="dot dot-red"></span>${r} Rejected</span>`;
  if(m) h += `<span class="flex items-center gap-1"><span class="dot dot-red"></span>${m} Missing</span>`;
  return h || `<span class="text-gray-400 text-xs">No docs</span>`;
}
function statusBadge(s){
  const normalized = s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;
  const full = {
    "Pending review":"Pending Review",
    "Under review":"Under Review"
  }[normalized] || normalized;
  const m={"Pending Review":"badge-pending","Under Review":"badge-review","Verified":"badge-verified","Incomplete":"badge-incomplete","Rejected":"badge-rejected"};
  const ic={"Pending Review":"⏳","Under Review":"🔄","Verified":"✅","Incomplete":"⚠️","Rejected":"❌"};
  return `<span class="status-badge ${m[full]||'badge-review'}">${ic[full]||''}${full}</span>`;
}
function initials(n){return n.split(" ").filter((_,i,a)=>i===0||i===a.length-1).map(x=>x[0]).join("").toUpperCase();}
function avatarBg(n){const c=["bg-red-200 text-red-800","bg-blue-200 text-blue-800","bg-green-200 text-green-800","bg-purple-200 text-purple-800","bg-yellow-200 text-yellow-800"];return c[n.charCodeAt(0)%c.length];}

function showToast(msg,type="success"){
  const t=document.getElementById("toast");
  const ic=document.getElementById("toastIcon");
  document.getElementById("toastText").innerText=msg;
  ic.setAttribute("data-lucide",type==="success"?"check-circle":"alert-triangle");
  ic.className="w-4 h-4 "+(type==="success"?"text-green-400":"text-yellow-400");
  lucide.createIcons();
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>t.classList.add("hidden"),3200);
}

/* ═══ NAV ═══ */
function switchPage(pageId, el) {
  // Ensure data is initialized from context
  initializeData();
  
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const targetPage = document.getElementById('page-' + pageId);
  if (targetPage) targetPage.classList.add('active');
  
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (el) el.classList.add('active');
  
  if (pageId === 'documents') {
    if (typeof switchDocVerTab === 'function') {
      switchDocVerTab('application');
    }
    renderTable();
  }
  if (pageId === 'students') renderStudents();
  if (pageId === 'history') renderHistory();
  if (pageId === 'dashboard') renderDashboard();
  if (pageId === 'school-year') {
    loadSummary();
    renderSchoolYears('active');
    filterArchivedYears();
  }
  if (pageId === 'prospectus') renderProspectusPage();
  if (pageId === 'student-messaging' && typeof initMessagingPage === 'function') {
    setTimeout(initMessagingPage, 100);
  }
  
  lucide.createIcons();
}

/* ═══ DASHBOARD ═══ */
function renderDashboard(){
  // Render Recent Applications
  const recentAppsContainer = document.getElementById('dashRecentList');
  if(recentAppsContainer && contextData.recentApplications) {
    recentAppsContainer.innerHTML = contextData.recentApplications.map(app => `
      <div class="flex items-center justify-between p-4 hover:bg-gray-50 transition border-b border-gray-100 last:border-0">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full ${avatarBg(app.name)} flex items-center justify-center text-sm font-bold">${initials(app.name)}</div>
          <div>
            <p class="font-semibold text-gray-800 text-sm">${app.name}</p>
            <p class="text-xs text-gray-400">${app.id}</p>
          </div>
        </div>
        ${statusBadge(app.status)}
      </div>
    `).join('');
  }
  
  // Render Verification Progress
  const verificationContainer = document.getElementById('dashProgress');
  if(verificationContainer && contextData.verificationProgress) {
    const vp = contextData.verificationProgress;
    const items = [
      {name:'Verified',    count:vp.verified||0,  color:'#22c55e'},
      {name:'Under Review',count:vp.reviewing||0, color:'#eab308'},
      {name:'Pending',     count:vp.pending||0,   color:'#f97316'},
      {name:'Rejected',    count:vp.rejected||0,  color:'#ef4444'}
    ];
    const total = items.reduce((s,i)=>s+i.count,0)||1;
    verificationContainer.innerHTML = items.map(item=>{
      const pct = Math.round((item.count/total)*100);
      return `
        <div>
          <div class="flex justify-between items-center mb-1">
            <p class="text-xs text-gray-600 font-medium">${item.name}</p>
            <p class="text-xs font-semibold text-gray-800">${pct}%</p>
          </div>
          <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div style="width:${pct}%;background:${item.color}" class="h-full rounded-full transition"></div>
          </div>
        </div>`;
    }).join('');
  }
  
  lucide.createIcons();
}

/* ═══ DOCUMENTS TABLE ═══ */
function renderTable(){
  const tbody=document.getElementById("tableBody");
  const empty=document.getElementById("emptyState");
  if(!tbody) return;
  tbody.innerHTML="";
  const search=(document.getElementById("searchInput")?.value||"").toLowerCase();
  const filter=document.getElementById("statusFilter")?.value||"all";
  let filtered=applications.filter(a=>a.name.toLowerCase().includes(search)&&(filter==="all"||a.status===filter));
  if(!filtered.length){empty?.classList.remove("hidden");}
  else{
    empty?.classList.add("hidden");
    filtered.forEach(app=>{
      // Account status
      const isActive = app.accountActive !== undefined ? app.accountActive : true;
      const esc = (s) => String(s||'').replace(/'/g,"\\'");
      const userId = app.userId || 0;
      const reason = esc(app.accountStatusReason || '');
      const changedBy = esc(app.accountStatusChangedBy || '');
      const changedAt = esc(app.accountStatusChangedAt || '');
      
      tbody.innerHTML+=`
        <tr class="border-t border-gray-50 hover:bg-gray-50/70 transition-colors" data-app-id="${app.id}">
          <td class="px-4 py-4 text-red-700 font-semibold text-sm">${app.id}</td>
          <td class="px-4 py-4"><p class="font-semibold text-gray-800 text-sm">${app.name}</p><p class="text-xs text-gray-400">${app.email}</p><p class="text-xs text-gray-400">${app.mobile}</p></td>
          <td class="px-4 py-4 text-sm text-gray-700">${app.course}</td>
          <td class="px-4 py-4"><div class="flex flex-col gap-0.5 text-xs text-gray-600">${getDocStatus(app.docs)}</div></td>
          <td class="px-4 py-4">${statusBadge(app.status)}</td>
          <td class="px-4 py-4 text-xs text-gray-400">${app.last_activity}</td>
          <td class="px-4 py-4">
            <div class="flex items-center gap-2">
              <button onclick="openApplicationTab('${app.id}')" class="flex items-center gap-1.5 bg-gray-100 text-gray-800 text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-gray-200 transition"><i data-lucide="file-text" class="w-3.5 h-3.5"></i> Details</button>
              <button onclick="openModal('${app.id}')" class="flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-gray-700 transition"><i data-lucide="eye" class="w-3.5 h-3.5"></i> Review</button>
              <button onclick="deleteApp('${app.id}')" class="w-7 h-7 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
            </div>
          </td>
        </tr>`;
    });
  }
  updateCounts();
  lucide.createIcons();
}



function updateCounts(){
  const s = applications.map(a=>(a.status||'').toLowerCase());
  document.getElementById("totalCount").innerText     =applications.length;
  document.getElementById("pendingCount").innerText   =s.filter(x=>x==="pending review").length;
  document.getElementById("reviewCount").innerText    =s.filter(x=>x==="under review").length;
  document.getElementById("verifiedCount").innerText  =s.filter(x=>x==="verified").length;
  document.getElementById("incompleteCount").innerText=s.filter(x=>x==="incomplete").length;
}
/* ═══ STUDENTS ═══ */
function renderStudents(){
  const grid=document.getElementById("studentGrid");
  const cnt=document.getElementById("studentCount");
  if(!grid) return;
  const search=(document.getElementById("studentSearch")?.value||"").toLowerCase();
  const course=document.getElementById("studentCourse")?.value||"all";
  let filtered=applications.filter(a=>
    (a.name.toLowerCase().includes(search)||a.id.toLowerCase().includes(search))&&
    (course==="all"||a.course===course)
  );
  if(cnt) cnt.innerText=filtered.length;
  if(!filtered.length){
    grid.innerHTML=`<div class="col-span-3 py-16 text-center text-gray-400"><i data-lucide="inbox" class="w-10 h-10 mx-auto mb-2 opacity-40"></i><p class="text-sm">No students found.</p></div>`;
    lucide.createIcons(); return;
  }
  grid.innerHTML=filtered.map(app=>{
    // Account status
    const isActive = app.accountActive !== undefined ? app.accountActive : true;
    const accountBadge = isActive 
      ? '<span class="px-2 py-0.5 text-xs rounded-full bg-green-50 border border-green-200 text-green-700 font-medium">Active</span>'
      : '<span class="px-2 py-0.5 text-xs rounded-full bg-red-50 border border-red-200 text-red-700 font-medium">Inactive</span>';
    
    const esc = (s) => String(s||'').replace(/'/g,"\\'");
    const userId = app.userId || 0;
    const reason = esc(app.accountStatusReason || '');
    const changedBy = esc(app.accountStatusChangedBy || '');
    const changedAt = esc(app.accountStatusChangedAt || '');
    
    const toggleBtn = `
      <button onclick="openToggleStatusModal(${userId},'${esc(app.name)}',${isActive},'${reason}','${changedBy}','${changedAt}')" 
        class="text-xs font-medium px-3 py-1.5 rounded-lg border transition flex items-center gap-1.5 w-full justify-center
        ${isActive ? 'text-red-600 border-red-200 hover:bg-red-50' : 'text-green-600 border-green-200 hover:bg-green-50'}">
        <i data-lucide="${isActive ? 'user-x' : 'user-check'}" class="w-3 h-3"></i>
        ${isActive ? 'Deactivate Account' : 'Activate Account'}
      </button>`;
    
    const statusInfo = app.accountStatusReason 
      ? `<p class="text-xs text-gray-400 mt-1.5">${esc(app.accountStatusChangedBy||'')}${app.accountStatusChangedBy && app.accountStatusChangedAt ? ' · ' : ''}${esc(app.accountStatusChangedAt||'')}</p>`
      : '';
    
    return `
    <div class="bg-white rounded-2xl shadow-sm p-5 fade-in hover:shadow-md transition">
      <div class="flex items-center gap-4 mb-3">
        <div class="w-12 h-12 rounded-full ${avatarBg(app.name)} flex items-center justify-center font-bold text-base flex-shrink-0">${initials(app.name)}</div>
        <div>
          <p class="font-bold text-gray-800 text-sm leading-tight">${app.name}</p>
          <p class="text-xs text-gray-400">${app.course} · ${app.id}</p>
        </div>
      </div>
      <div class="mb-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
        <div class="flex items-center justify-between mb-1.5">
          <span class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Account</span>
          ${accountBadge}
        </div>
        ${statusInfo}
        <div class="mt-2">${toggleBtn}</div>
      </div>
      <div class="space-y-1.5 text-xs text-gray-500 mb-3">
        <p class="flex items-center gap-2"><i data-lucide="mail" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>${app.email}</p>
        <p class="flex items-center gap-2"><i data-lucide="phone" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>${app.mobile}</p>
        <p class="flex items-center gap-2"><i data-lucide="calendar" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>Submitted: ${app.submission_date}</p>
      </div>
      <div class="border-t border-gray-100 pt-3 flex items-center justify-between">
        ${statusBadge(app.status)}
        <button onclick="switchPage('documents',document.querySelectorAll('.nav-item')[1]);setTimeout(function(){openModal('${app.id}')},120)"
          class="text-xs text-red-700 font-semibold hover:underline flex items-center gap-1"><i data-lucide="eye" class="w-3 h-3"></i> View Docs</button>
      </div>
    </div>`;
  }).join("");
  lucide.createIcons();
}

/* ═══ BULK VERIFY FUNCTIONS ═══ */

function toggleSelectAllApps() {
  const selectAll = document.getElementById('selectAllApps');
  const checkboxes = document.querySelectorAll('.app-select-checkbox');
  checkboxes.forEach(cb => {
    cb.checked = selectAll.checked;
  });
}

function getSelectedAppIds() {
  const checkboxes = document.querySelectorAll('.app-select-checkbox:checked');
  return Array.from(checkboxes).map(cb => cb.dataset.appId);
}

async function bulkVerifyApplications() {
  const selectedIds = getSelectedAppIds();
  
  if (selectedIds.length === 0) {
    showToast('Please select at least one application to verify', 'warn');
    return;
  }
  
  if (!confirm(`Are you sure you want to bulk verify ${selectedIds.length} application(s)?`)) return;
  
  let successCount = 0;
  let failCount = 0;
  
  for (const appId of selectedIds) {
    try {
      const response = await fetch('/admin-panel/api/application/bulk-verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ application_id: appId })
      });
      const data = await response.json();
      
      if (data.success) {
        const app = applications.find(a => a.id === appId);
        if (app) app.status = 'Verified';
        successCount++;
      } else {
        failCount++;
      }
    } catch (error) {
      failCount++;
    }
  }
  
  showToast(`Verified: ${successCount}, Failed: ${failCount}`, successCount > 0 ? 'success' : 'warn');
  renderTable();
}

/* ═══ REVIEW MODAL ═══ */
function openModal(id){
  console.log('openModal called with id:', id);
  console.log('Current applications array:', applications);
  selectedApp=applications.find(a=>a.id===id);
  console.log('Selected app:', selectedApp);
  if(!selectedApp) {
    console.error('Application not found with id:', id);
    alert('Error: Could not find application with ID ' + id);
    return;
  }
  document.getElementById("modalID").innerText =selectedApp.id;
  document.getElementById("mName").innerText   =selectedApp.name;
  document.getElementById("mEmail").innerText  =selectedApp.email;
  document.getElementById("mCourse").innerText =selectedApp.course;
  document.getElementById("mMobile").innerText =selectedApp.mobile;
  document.getElementById("mAppID").innerText  =selectedApp.id;
  document.getElementById("mDate").innerText   =selectedApp.submission_date;
  document.getElementById("lastUpdated").innerText="Last updated: "+new Date().toISOString().split("T")[0];
  document.getElementById("remarks").value     =selectedApp.remarks||"";
  // Populate admission details
  const semEl = document.getElementById("admSemester");
  const yearEl = document.getElementById("admYear");
  const levelEl = document.getElementById('admProgramLevel');
  const currEl = document.getElementById("admCurriculum");
  if(semEl) semEl.value   = selectedApp.semester   || "";
  if(yearEl) yearEl.value = selectedApp.year_admitted || "";
  if(levelEl) levelEl.value = selectedApp.program_level || "";
  if(currEl) currEl.value = selectedApp.student_curriculum || selectedApp.curriculum  || "";
  renderDocCards();
  const modal = document.getElementById("modal");
  if(modal) {
    modal.classList.add("open");
    modal.style.display = "flex";
    console.log('Modal opened successfully');
  } else {
    console.error('Modal element not found');
  }
}
function closeModal(){
  const modal = document.getElementById("modal");
  if(modal) {
    modal.classList.remove("open");
    modal.style.display = "none";
  }
}

/* ═══ DOCUMENT PREVIEW HELPERS ═══ */
let docPreviewCurrentIdx = 0;

function getFileExt(url){
  const clean = (url||'').split('?')[0];
  return clean.split('.').pop().toLowerCase();
}

function getDocumentPreviewMarkup(doc, size='thumb'){
  const url = doc.fileUrl || '';
  const ext = getFileExt(url);
  const imageExts = ['jpg','jpeg','png','webp','gif'];
  const pdfExts   = ['pdf'];
  const h = size === 'full' ? 'h-full' : 'h-full';

  if(!url){
    return `<div class="w-full h-full flex flex-col items-center justify-center gap-2 text-gray-400 select-none">
      <i data-lucide="file-x" class="w-8 h-8 opacity-40"></i>
      <p class="text-xs font-semibold">No file attached</p>
    </div>`;
  }

  if(imageExts.includes(ext)){
    if(size === 'full'){
      return `<img src="${url}" alt="${doc.name}"
        class="max-w-full max-h-full object-contain rounded-lg shadow-md cursor-zoom-in"
        onclick="window.open('${url}','_blank')" />`;
    }
    return `<img src="${url}" alt="${doc.name}"
      class="w-full h-full object-cover cursor-pointer hover:opacity-90 transition"
      onclick="openDocPreview(${doc._idx})" />`;
  }

  if(pdfExts.includes(ext)){
    if(size === 'full'){
      return `<iframe src="${url}#toolbar=0&navpanes=0&view=FitH" class="w-full h-full rounded-lg border-0"
        title="${doc.name}">
        <div class="w-full h-full flex flex-col items-center justify-center gap-2 text-gray-500 bg-gray-100 rounded-lg">
          <i data-lucide="file-text" class="w-10 h-10 opacity-40"></i>
          <p class="text-sm font-semibold">PDF cannot be rendered inline.</p>
          <a href="${url}" target="_blank" class="text-sm text-red-700 underline font-semibold mt-1">Open in new tab →</a>
        </div>
      </iframe>`;
    }
    return `<div class="w-full h-full flex flex-col items-center justify-center gap-1.5 text-gray-500 cursor-pointer hover:bg-gray-200 transition rounded-lg"
      onclick="openDocPreview(${doc._idx})">
      <i data-lucide="file-text" class="w-7 h-7 text-red-400"></i>
      <p class="text-[11px] font-semibold text-gray-600">PDF Preview</p>
      <p class="text-[10px] text-gray-400">Click to view</p>
    </div>`;
  }

  return `<div class="w-full h-full flex flex-col items-center justify-center gap-2 text-gray-400 cursor-pointer hover:bg-gray-200 transition rounded-lg"
    onclick="openDocPreview(${doc._idx})">
    <i data-lucide="file" class="w-7 h-7 opacity-50"></i>
    <p class="text-[11px] font-semibold">Click to preview</p>
  </div>`;
}

/* ── Full-screen doc preview modal ── */
function openDocPreview(idx){
  docPreviewCurrentIdx = idx;
  _renderDocPreviewModal();
  const overlay = document.getElementById('docPreviewOverlay');
  overlay.style.display = 'flex';
  lucide.createIcons();
}

function closeDocPreview(){
  document.getElementById('docPreviewOverlay').style.display = 'none';
}

function navDocPreview(dir){
  const total = selectedApp.docs.length;
  let next = (docPreviewCurrentIdx + dir + total) % total;
  // Skip missing docs when navigating
  let attempts = 0;
  while(selectedApp.docs[next].missing && attempts < total){
    next = (next + dir + total) % total;
    attempts++;
  }
  docPreviewCurrentIdx = next;
  _renderDocPreviewModal();
  lucide.createIcons();
}

function _renderDocPreviewModal(){
  const doc  = selectedApp.docs[docPreviewCurrentIdx];
  const total = selectedApp.docs.length;
  const isV  = doc.status === 'Verified';
  const isR  = doc.status === 'Rejected';

  // Header info
  document.getElementById('dpDocName').textContent    = doc.name;
  document.getElementById('dpDocType').textContent    = doc.type;
  document.getElementById('dpDocUploaded').textContent= doc.uploadDate;
  document.getElementById('dpDocCounter').textContent = `${docPreviewCurrentIdx+1} / ${total}`;

  // Badge
  const badgeEl = document.getElementById('dpDocBadge');
  if(isV) badgeEl.className='status-badge badge-verified', badgeEl.innerHTML='<i data-lucide="check-circle" class="w-3 h-3"></i>Verified';
  else if(isR) badgeEl.className='status-badge badge-rejected', badgeEl.innerHTML='<i data-lucide="x-circle" class="w-3 h-3"></i>Rejected';
  else badgeEl.className='status-badge badge-pending', badgeEl.innerHTML='<i data-lucide="clock" class="w-3 h-3"></i>'+doc.status;

  // Verified-by strip
  const vstrip = document.getElementById('dpVerifiedBy');
  if(isV && doc.verifiedBy){
    vstrip.classList.remove('hidden');
    vstrip.innerHTML=`<i data-lucide="user-check" class="w-3.5 h-3.5 text-green-500"></i><span class="text-green-700 text-xs font-medium">Verified by <strong>${doc.verifiedBy}</strong> on ${doc.verifiedOn}</span>`;
  } else { vstrip.classList.add('hidden'); }

  // Issues strip
  const istrip = document.getElementById('dpIssues');
  if(doc.issues && doc.issues.length){
    istrip.classList.remove('hidden');
    istrip.innerHTML=`<i data-lucide="alert-triangle" class="w-3.5 h-3.5 text-red-500 flex-shrink-0"></i><span class="text-red-600 text-xs">${doc.issues.join(' · ')}</span>`;
  } else { istrip.classList.add('hidden'); }

  // Preview area
  document.getElementById('dpPreviewArea').innerHTML = getDocumentPreviewMarkup(doc, 'full');

  // Action buttons
  const actionsEl = document.getElementById('dpActions');
  if(!isV && !isR){
    actionsEl.innerHTML=`
      <button onclick="verifyDoc(${docPreviewCurrentIdx}); _renderDocPreviewModal();" class="flex items-center gap-1.5 bg-green-500 hover:bg-green-600 text-white text-xs font-semibold px-4 py-2 rounded-xl transition">
        <i data-lucide="check" class="w-3.5 h-3.5"></i> Verify
      </button>
      <button onclick="rejectDoc(${docPreviewCurrentIdx})" class="flex items-center gap-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold px-4 py-2 rounded-xl transition">
        <i data-lucide="x" class="w-3.5 h-3.5"></i> Reject
      </button>`;
  } else {
    actionsEl.innerHTML=`

        if(levelEl && targetProgramLevel){
          levelEl.value = targetProgramLevel;
        }
      <button onclick="unsetDoc(${docPreviewCurrentIdx}); _renderDocPreviewModal();" class="flex items-center gap-1.5 border border-gray-300 text-gray-600 text-xs font-semibold px-4 py-2 rounded-xl hover:bg-gray-50 transition">
        <i data-lucide="rotate-ccw" class="w-3.5 h-3.5"></i> ${isV ? 'Undo Verify' : 'Undo Reject'}
      </button>`;
  }

  // Open full button
  document.getElementById('dpOpenFull').onclick = ()=> viewFullDoc(doc.fileUrl, doc.name);

  // Nav buttons
  document.getElementById('dpNavPrev').classList.toggle('invisible', total <= 1);
  document.getElementById('dpNavNext').classList.toggle('invisible', total <= 1);

  lucide.createIcons();
}

/* inject the doc preview overlay HTML once */
(function injectDocPreviewOverlay(){
  if(document.getElementById('docPreviewOverlay')) return;
  const html = `
  <div id="docPreviewOverlay" style="display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,0.72);align-items:center;justify-content:center;padding:1rem;backdrop-filter:blur(4px)">
    <div style="background:#fff;border-radius:1.5rem;width:100%;max-width:860px;max-height:92vh;display:flex;flex-direction:column;overflow:hidden;box-shadow:0 32px 64px rgba(0,0,0,.35)">
      <!-- Header -->
      <div style="display:flex;align-items:flex-start;justify-content:space-between;padding:1.1rem 1.4rem 0.9rem;border-bottom:1px solid #f3f4f6;flex-shrink:0">
        <div style="min-width:0;flex:1">
          <div style="display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.3rem">
            <p id="dpDocName" style="font-weight:700;font-size:0.95rem;color:#1f2937;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:380px"></p>
            <span id="dpDocBadge" class="status-badge badge-pending"></span>
          </div>
          <div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap">
            <p style="font-size:0.72rem;color:#9ca3af"><span style="font-weight:600;color:#6b7280">Type:</span> <span id="dpDocType"></span></p>
            <p style="font-size:0.72rem;color:#9ca3af"><span style="font-weight:600;color:#6b7280">Uploaded:</span> <span id="dpDocUploaded"></span></p>
            <p style="font-size:0.72rem;color:#9ca3af" id="dpDocCounter"></p>
          </div>
          <div id="dpVerifiedBy" class="hidden" style="display:flex;align-items:center;gap:0.4rem;margin-top:0.4rem;padding:0.3rem 0.7rem;background:#f0fdf4;border-radius:0.5rem;width:fit-content"></div>
          <div id="dpIssues" class="hidden" style="display:flex;align-items:center;gap:0.4rem;margin-top:0.4rem;padding:0.3rem 0.7rem;background:#fef2f2;border-radius:0.5rem"></div>
        </div>
        <button onclick="closeDocPreview()" style="width:2rem;height:2rem;border-radius:50%;border:none;background:#f3f4f6;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:1.1rem;color:#6b7280;flex-shrink:0;margin-left:0.75rem" onmouseover="this.style.background='#e5e7eb'" onmouseout="this.style.background='#f3f4f6'">&times;</button>
      </div>

      <!-- Preview area -->
      <div style="flex:1;overflow:hidden;position:relative;background:#f8fafc;display:flex;align-items:center;justify-content:center;min-height:0">
        <!-- Nav prev -->
        <button id="dpNavPrev" onclick="navDocPreview(-1)" style="position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);z-index:10;width:2.25rem;height:2.25rem;border-radius:50%;background:rgba(255,255,255,0.9);border:1px solid #e5e7eb;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,.12)" onmouseover="this.style.background='#fff'" onmouseout="this.style.background='rgba(255,255,255,0.9)'">
          <i data-lucide="chevron-left" style="width:1rem;height:1rem;color:#374151"></i>
        </button>
        <!-- Preview content -->
        <div id="dpPreviewArea" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:1rem;overflow:auto"></div>
        <!-- Nav next -->
        <button id="dpNavNext" onclick="navDocPreview(1)" style="position:absolute;right:0.75rem;top:50%;transform:translateY(-50%);z-index:10;width:2.25rem;height:2.25rem;border-radius:50%;background:rgba(255,255,255,0.9);border:1px solid #e5e7eb;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,.12)" onmouseover="this.style.background='#fff'" onmouseout="this.style.background='rgba(255,255,255,0.9)'">
          <i data-lucide="chevron-right" style="width:1rem;height:1rem;color:#374151"></i>
        </button>
      </div>

      <!-- Footer actions -->
      <div style="display:flex;align-items:center;justify-content:space-between;padding:0.85rem 1.4rem;border-top:1px solid #f3f4f6;flex-shrink:0;gap:0.75rem;flex-wrap:wrap">
        <div id="dpActions" style="display:flex;gap:0.6rem;flex-wrap:wrap"></div>
        <button id="dpOpenFull" style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 1rem;border:1px solid #e5e7eb;border-radius:0.75rem;background:#fff;color:#374151;font-size:0.75rem;font-weight:600;cursor:pointer;transition:background .15s" onmouseover="this.style.background='#f9fafb'" onmouseout="this.style.background='#fff'">
          <i data-lucide="external-link" style="width:0.875rem;height:0.875rem"></i> Open in New Tab
        </button>
      </div>
    </div>
  </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
  // Close on backdrop click
  document.getElementById('docPreviewOverlay').addEventListener('click', function(e){
    if(e.target === this) closeDocPreview();
  });
})();

function renderDocCards(){
  const container = document.getElementById("docCards");
  container.innerHTML = "";

  if(!selectedApp.docs || selectedApp.docs.length === 0){
    container.innerHTML = `<div class="col-span-full py-10 text-center text-gray-400">
      <i data-lucide="inbox" class="w-8 h-8 mx-auto mb-2 opacity-40"></i>
      <p class="text-sm">No documents submitted yet.</p></div>`;
    lucide.createIcons(); return;
  }

  selectedApp.docs.forEach((doc, idx) => {
    doc._idx = idx;

    // ── MISSING document card ──────────────────────────────────────────────
    if(doc.missing || doc.status === 'Missing'){
      container.innerHTML += `
        <div class="doc-card border-2 border-dashed border-red-300 bg-red-50/40 rounded-2xl p-4 flex flex-col text-sm">
          <div class="flex items-start justify-between gap-2 mb-3">
            <p class="font-semibold text-gray-800 text-xs leading-snug flex-1">${doc.name}</p>
            <span class="status-badge" style="background:#fee2e2;color:#b91c1c;border:1px solid #fca5a5;display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap">
              <i data-lucide="alert-circle" class="w-3 h-3"></i>Missing
            </span>
          </div>
          <!-- Placeholder thumbnail -->
          <div class="rounded-xl overflow-hidden mb-3 flex flex-col items-center justify-center bg-red-100/60 border border-dashed border-red-300"
               style="height:140px">
            <i data-lucide="file-x" class="w-8 h-8 text-red-400 mb-1.5"></i>
            <p class="text-[11px] font-semibold text-red-500">Not Submitted</p>
            <p class="text-[10px] text-red-400 mt-0.5">Awaiting student upload</p>
          </div>
          <!-- Meta -->
          <p class="text-[11px] text-gray-500"><span class="font-semibold text-gray-600">Type:</span> ${doc.type}</p>
          <p class="text-[11px] text-red-400 mt-0.5 flex items-center gap-1">
            <i data-lucide="clock" class="w-3 h-3"></i> Student has not uploaded this document
          </p>
          <!-- Action: notify student -->
          <button
            onclick="notifyMissingDoc('${doc.docType}', '${doc.name}')"
            class="w-full mt-3 flex items-center justify-center gap-1.5 border border-red-300 text-red-600 text-xs font-semibold py-2 rounded-xl hover:bg-red-50 transition">
            <i data-lucide="bell" class="w-3.5 h-3.5"></i> Notify Student
          </button>
        </div>`;
      return; // skip the rest for missing docs
    }

    // ── SUBMITTED document card (existing logic) ───────────────────────────
    const isV = doc.status === "Verified";
    const isR = doc.status === "Rejected";
    const border = isV ? "border-green-300 bg-green-50/30" : isR ? "border-red-300 bg-red-50/30" : "border-orange-200 bg-orange-50/20";
    const badge = isV
      ? `<span class="status-badge badge-verified"><i data-lucide="check-circle" class="w-3 h-3"></i>Verified</span>`
      : isR
      ? `<span class="status-badge badge-rejected"><i data-lucide="x-circle" class="w-3 h-3"></i>Rejected</span>`
      : `<span class="status-badge badge-review"><i data-lucide="clock" class="w-3 h-3"></i>${doc.status}</span>`;
    const issues = doc.issues && doc.issues.length
      ? `<div class="mt-1.5 px-2 py-1.5 bg-red-50 rounded-lg">
          <p class="text-[11px] font-semibold text-red-500 mb-0.5">Issues:</p>
          ${doc.issues.map(i => `<p class="text-[11px] text-red-500 flex items-start gap-1"><span>•</span>${i}</p>`).join("")}
        </div>` : "";
    const verInfo = isV && doc.verifiedBy
      ? `<p class="text-[11px] text-green-600 mt-1 flex items-center gap-1">
          <i data-lucide="user-check" class="w-3 h-3"></i>${doc.verifiedBy} · ${doc.verifiedOn}</p>` : "";
    const btns = !isV && !isR
      ? `<div class="flex gap-2 mt-3">
          <button onclick="verifyDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white text-xs font-semibold py-2 rounded-xl hover:bg-green-600 transition shadow-sm">
            <i data-lucide="check" class="w-3 h-3"></i> Verify</button>
          <button onclick="rejectDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-red-500 text-white text-xs font-semibold py-2 rounded-xl hover:bg-red-600 transition shadow-sm">
            <i data-lucide="x" class="w-3 h-3"></i> Reject</button>
        </div>`
      : `<button onclick="unsetDoc(${idx})" class="w-full mt-3 text-xs text-gray-500 border border-gray-200 rounded-xl py-2 hover:bg-gray-50 transition">
          ${isV ? "↩ Undo Verify" : "↩ Undo Reject"}</button>`;

    const ext = getFileExt(doc.fileUrl || '');
    const isPdf = ext === 'pdf';
    const previewLabel = isPdf
      ? `<span style="position:absolute;top:6px;left:6px;background:rgba(239,68,68,0.9);color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:4px;letter-spacing:.04em">PDF</span>`
      : '';

    container.innerHTML += `
      <div class="doc-card border-2 ${border} rounded-2xl p-4 flex flex-col text-sm transition-shadow">
        <div class="flex items-start justify-between gap-2 mb-3">
          <p class="font-semibold text-gray-800 text-xs leading-snug flex-1">${doc.name}</p>
          ${badge}
        </div>
        <div class="relative rounded-xl overflow-hidden mb-3 cursor-pointer group" style="height:140px;background:#f3f4f6"
          onclick="openDocPreview(${idx})">
          ${getDocumentPreviewMarkup(doc, 'thumb')}
          ${previewLabel}
          <div style="position:absolute;inset:0;background:rgba(0,0,0,0);transition:background .2s;display:flex;align-items:center;justify-content:center"
            class="group-hover:bg-black/20">
            <span style="opacity:0;transition:opacity .2s;background:rgba(0,0,0,0.65);color:#fff;font-size:11px;font-weight:600;padding:5px 12px;border-radius:8px;display:flex;align-items:center;gap:5px"
              class="group-hover:opacity-100">
              <i data-lucide="maximize-2" style="width:12px;height:12px"></i> Preview
            </span>
          </div>
        </div>
        <p class="text-[11px] text-gray-500"><span class="font-semibold text-gray-600">Type:</span> ${doc.type}</p>
        <p class="text-[11px] text-gray-500"><span class="font-semibold text-gray-600">Uploaded:</span> ${doc.uploadDate}</p>
        ${verInfo}${issues}
        ${btns}
        <button onclick="openDocPreview(${idx})" class="mt-2 w-full flex items-center justify-center gap-1.5 border border-gray-200 text-gray-600 text-xs py-1.5 rounded-xl hover:bg-gray-50 transition">
          <i data-lucide="eye" class="w-3.5 h-3.5"></i> View Full
        </button>
      </div>`;
  });

  lucide.createIcons();
}

function verifyDoc(idx){
  const doc=selectedApp.docs[idx];
  fetch('/admin-panel/api/document/verify/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      document_id: doc.id
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      doc.status="Verified";
      doc.verifiedBy=contextData.adminName||"Admin";
      doc.verifiedOn=new Date().toISOString().split("T")[0];
      doc.issues=[];
      showToast(data.message);
      renderDocCards();
      if(document.getElementById('docPreviewOverlay')?.style.display==='flex') _renderDocPreviewModal();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}
function unsetDoc(idx){
  const doc=selectedApp.docs[idx];
  fetch('/admin-panel/api/document/reset/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      document_id: doc.id
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      doc.status="Under Review";
      doc.verifiedBy="";
      doc.verifiedOn="";
      doc.issues=[];
      showToast(data.message);
      renderDocCards();
      if(document.getElementById('docPreviewOverlay')?.style.display==='flex') _renderDocPreviewModal();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}

function viewFullDoc(fileUrl, docName){
  if(!fileUrl) {
    showToast("Document file not available","error");
    return;
  }
  window.open(fileUrl, '_blank');
  showToast(`Opening \"${docName}\"...`);
}

/* ═══ REJECT MODAL ═══ */
function rejectDoc(idx){
  rejectTargetIdx=idx;
  const doc=selectedApp.docs[idx];
  document.getElementById("rejectDocName").innerText=doc.name+" — "+doc.type;
  document.getElementById("rejectReason").value=doc.issues.length?doc.issues[0]:"";
  document.getElementById("rejectError").classList.add("hidden");
  document.querySelectorAll(".chip").forEach(c=>c.classList.remove("selected"));
  if(doc.issues.length) document.querySelectorAll(".chip").forEach(c=>{if(c.dataset.reason===doc.issues[0]) c.classList.add("selected");});
  const rejectModal = document.getElementById("rejectModal");
  rejectModal.classList.add("open");
  rejectModal.style.display = "flex";
  lucide.createIcons();
}
function closeRejectModal(){
  const modal = document.getElementById("rejectModal");
  if(modal) {
    modal.classList.remove("open");
    modal.style.display = "none";
  }
  rejectTargetIdx = null;
}
function selectChip(el){
  document.querySelectorAll(".chip").forEach(c=>c.classList.remove("selected"));
  el.classList.add("selected");
  document.getElementById("rejectReason").value=el.dataset.reason;
  document.getElementById("rejectError").classList.add("hidden");
}
function confirmReject(){
  const reason=document.getElementById("rejectReason").value.trim();
  if(!reason){document.getElementById("rejectError").classList.remove("hidden");return;}
  
  const doc=selectedApp.docs[rejectTargetIdx];
  fetch('/admin-panel/api/document/reject/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      document_id: doc.id,
      reason: reason
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.docs[rejectTargetIdx].status="Rejected";
      selectedApp.docs[rejectTargetIdx].issues=[reason];
      showToast("Document rejected: "+reason.substring(0,40)+(reason.length>40?"…":""),"warn");
      closeRejectModal();
      renderDocCards();
      if(document.getElementById('docPreviewOverlay')?.style.display==='flex') _renderDocPreviewModal();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}

/* ═══ MODAL ACTIONS ═══ */
function markVerified(){
  const remarks    = document.getElementById("remarks").value;
  const semester   = document.getElementById("admSemester")?.value  || "";
  const yearAdmitted = document.getElementById("admYear")?.value    || "";
  const curriculum = document.getElementById("admCurriculum")?.value || "";

  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'verified',
      remarks,
      semester,
      year_admitted: yearAdmitted,
      curriculum,
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.remarks       = remarks;
      selectedApp.status        = "Verified";
      selectedApp.semester      = semester;
      selectedApp.year_admitted = yearAdmitted;
      selectedApp.curriculum    = curriculum;
      showToast(selectedApp.id+" marked as Verified ✓");
      closeModal();
      initializeData();
      renderTable();
      renderDashboard();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}
function markIncomplete(){
  const remarks=document.getElementById("remarks").value;
  
  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'incomplete',
      remarks: remarks
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.remarks=remarks;
      selectedApp.status="Incomplete";
      showToast(selectedApp.id+" marked as Incomplete","warn");
      closeModal();
      initializeData();
      renderTable();
      renderDashboard();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}
function requestResubmission(){
  activityLog.unshift({time:new Date().toLocaleString(),admin:"Marwina Admin",appId:selectedApp?.id||"",doc:"Application",action:"Resubmission",notes:"Resubmission request sent."});
  showToast("Resubmission request sent to student","warn");
}

function acceptEnrollApplication(){
  if(!selectedApp) return showToast('No application selected','error');
  if(!confirm('Accept application '+selectedApp.id+' and mark as Enrolled?')) return;
  const remarks    = document.getElementById("remarks")?.value || '';
  const semester   = document.getElementById("admSemester")?.value  || "";
  const yearAdmitted = document.getElementById("admYear")?.value    || "";
  const programLevel = document.getElementById("admProgramLevel")?.value || "";

  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'enrolled',
      remarks,
      semester,
      year_admitted: yearAdmitted,
      program_level: programLevel
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.remarks = remarks;
      selectedApp.status = 'Enrolled';
      selectedApp.semester = semester;
      selectedApp.year_admitted = yearAdmitted;
      selectedApp.program_level = programLevel;
      showToast(selectedApp.id+" accepted — status set to Enrolled ✓");
      closeModal();
      initializeData(); renderTable(); renderDashboard();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}

function rejectEnrollApplication(){
  if(!selectedApp) return showToast('No application selected','error');
  if(!confirm('Reject application '+selectedApp.id+'?')) return;
  const remarks=document.getElementById("remarks")?.value || '';

  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'rejected',
      remarks: remarks
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.remarks=remarks;
      selectedApp.status="Rejected";
      showToast(selectedApp.id+" rejected","warn");
      closeModal();
      initializeData(); renderTable(); renderDashboard();
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}
function deleteApp(id){
  if(!confirm("Delete application "+id+"?")) return;
  applications=applications.filter(a=>a.id!==id);
  showToast("Application "+id+" deleted","warn");
  renderTable(); renderDashboard();
}
function exportCSV(){
  const rows=[["ID","Name","Course","Status","Last Activity"]];
  applications.forEach(a=>rows.push([a.id,a.name,a.course,a.status,a.last_activity]));
  const csv=rows.map(r=>r.join(",")).join("\n");
  const a=document.createElement("a");
  a.href="data:text/csv;charset=utf-8,"+encodeURIComponent(csv);
  a.download="applications.csv"; a.click();
  showToast("CSV exported");
}
function handleLogout(){
  if(confirm("Log out of the admin panel?")) {
    // Redirect to logout endpoint
    window.location.href = '/admin-panel/logout/';
  }
}

/* ═══ BACKDROP CLOSE ═══ */
document.getElementById("modal").addEventListener("click",function(e){if(e.target===this) closeModal();});
document.getElementById("rejectModal").addEventListener("click",function(e){if(e.target===this) closeRejectModal();});

/* ═══ LIVE FILTERS ═══ */
document.getElementById("searchInput").addEventListener("input",renderTable);
document.getElementById("statusFilter").addEventListener("change",renderTable);

/* ═══ INIT ═══ */
document.addEventListener('DOMContentLoaded', function() {
  initializeData();
  renderDashboard();
  renderTable();
  renderStudents();
  renderHistory();
});

/* ═══ EDIT PROFILE MODAL ═══ */
function openEditProfileModal() {
  // Populate form with current user data
  const adminName = document.querySelector('h3.font-bold.text-gray-800.text-base').innerText;
  const adminEmail = document.querySelector('p.text-xs.text-gray-400:last-of-type').innerText;
  
  // Split name into first and last name
  const nameParts = adminName.trim().split(' ');
  const firstName = nameParts[0] || '';
  const lastName = nameParts.slice(1).join(' ') || '';
  
  document.getElementById('editFirstName').value = firstName;
  document.getElementById('editLastName').value = lastName;
  document.getElementById('editEmail').value = adminEmail;
  
  // Clear error messages
  document.getElementById('editProfileError').classList.add('hidden');
  document.getElementById('firstNameError').classList.add('hidden');
  document.getElementById('lastNameError').classList.add('hidden');
  document.getElementById('emailError').classList.add('hidden');
  
  // Show modal
  document.getElementById('editProfileModal').classList.add('open');
  document.getElementById('editProfileModal').style.display = 'flex';
}

function closeEditProfileModal() {
  document.getElementById('editProfileModal').classList.remove('open');
  document.getElementById('editProfileModal').style.display = 'none';
}

function handleEditProfile(event) {
  event.preventDefault();
  
  const firstName = document.getElementById('editFirstName').value.trim();
  const lastName = document.getElementById('editLastName').value.trim();
  const email = document.getElementById('editEmail').value.trim();
  
  // Clear previous errors
  document.getElementById('editProfileError').classList.add('hidden');
  document.getElementById('firstNameError').classList.add('hidden');
  document.getElementById('lastNameError').classList.add('hidden');
  document.getElementById('emailError').classList.add('hidden');
  
  // Validate inputs
  let hasError = false;
  if (!firstName) {
    document.getElementById('firstNameError').innerText = 'First name is required';
    document.getElementById('firstNameError').classList.remove('hidden');
    hasError = true;
  }
  if (!lastName) {
    document.getElementById('lastNameError').innerText = 'Last name is required';
    document.getElementById('lastNameError').classList.remove('hidden');
    hasError = true;
  }
  if (!email) {
    document.getElementById('emailError').innerText = 'Email is required';
    document.getElementById('emailError').classList.remove('hidden');
    hasError = true;
  }
  
  if (hasError) return;
  
  // Disable submit button during request
  const submitBtn = document.getElementById('saveProfileBtn');
  submitBtn.disabled = true;
  submitBtn.innerText = 'Saving...';
  
  // Send update request
  fetch('/admin-panel/api/admin/profile/update/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      email: email
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showToast('Profile updated successfully!', 'success');
      closeEditProfileModal();
      // You might want to refresh the page or update the UI here
      location.reload();
    } else {
      document.getElementById('editProfileError').innerText = data.message;
      document.getElementById('editProfileError').classList.remove('hidden');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    document.getElementById('editProfileError').innerText = 'An error occurred. Please try again.';
    document.getElementById('editProfileError').classList.remove('hidden');
  })
  .finally(() => {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> Save Changes';
    lucide.createIcons();
  });
}

/* ═══ PHOTO UPLOAD ═══ */
function triggerPhotoUpload() {
  document.getElementById('photoFileInput').click();
}

function handlePhotoUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    showToast('Only JPG, PNG, and WEBP images are allowed', 'warn');
    return;
  }
  
  // Validate file size (5MB)
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    showToast('File size must not exceed 5MB', 'warn');
    return;
  }
  
  // Create FormData for file upload
  const formData = new FormData();
  formData.append('photo', file);
  
  // Show uploading toast
  showToast('Uploading photo...', 'success');
  
  // Send upload request
  fetch('/admin-panel/api/admin/photo/upload/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken()
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showToast('Profile photo updated successfully!', 'success');
      // Update the avatar image with the new photo URL
      const avatarDiv = document.getElementById('adminAvatar');
      if (avatarDiv && data.data && data.data.photo_url) {
        // Clear the background color and add the image
        avatarDiv.classList.remove('bg-red-800');
        avatarDiv.innerHTML = `<img src="${data.data.photo_url}?t=${new Date().getTime()}" class="w-full h-full object-cover rounded-full" alt="Profile Photo">`;
      }
      // Reload page after short delay to update activity history
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast('Error: ' + data.message, 'warn');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showToast('Error uploading photo. Please try again.', 'warn');
  })
  .finally(() => {
    // Reset the file input
    event.target.value = '';
  });
}

// Handle backdrop close for edit profile modal
document.addEventListener('DOMContentLoaded', () => {
  const editProfileModal = document.getElementById('editProfileModal');
  if (editProfileModal) {
    editProfileModal.addEventListener('click', function(e) {
      if (e.target === this) {
        closeEditProfileModal();
      }
    });
  }
});
/* ═══ CMS SETTINGS ═══ */
function addAnnouncementRow() {
  const list = document.getElementById('announcementsList');
  const row = document.createElement('div');
  row.className = 'announcement-row flex items-center gap-2';
  row.innerHTML = `
    <input type="text" placeholder="Announcement text…"
      class="ann-text flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400 transition" />
    <input type="number" placeholder="sec" value="5" min="3" max="30"
      class="ann-duration w-16 border border-gray-200 rounded-lg px-2 py-2 text-sm text-center focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400 transition" />
    <button type="button" onclick="removeAnnouncementRow(this)"
      class="w-7 h-7 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition flex-shrink-0">
      <i data-lucide="x" class="w-4 h-4"></i>
    </button>`;
  list.appendChild(row);
  lucide.createIcons();
}

function removeAnnouncementRow(btn) {
  const list = document.getElementById('announcementsList');
  if (list.querySelectorAll('.announcement-row').length > 1) {
    btn.closest('.announcement-row').remove();
  }
}

function addProgramRow() {
  const list = document.getElementById('programsList');
  const row = document.createElement('div');
  row.className = 'program-row border border-gray-100 rounded-xl p-3 bg-gray-50 space-y-2';
  row.innerHTML = `
    <div class="flex items-center gap-2">
      <input type="text" placeholder="Program name e.g. Master in Information Technology"
        class="prog-name flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400 transition" />
      <button type="button" onclick="removeProgramRow(this)"
        class="w-7 h-7 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-100 rounded-lg transition flex-shrink-0">
        <i data-lucide="x" class="w-4 h-4"></i>
      </button>
    </div>
    <input type="text" placeholder="Degree type e.g. Master's Degree"
      class="prog-degree w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400 transition" />
    <textarea placeholder="Short description shown on the card…" rows="2"
      class="prog-desc w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-red-200 focus:border-red-400 transition resize-none"></textarea>
    <div class="flex items-center gap-2">
      <div class="toggle-track on prog-visible-toggle" onclick="this.classList.toggle('on')">
        <div class="toggle-thumb"></div>
      </div>
      <span class="text-xs text-gray-500">Visible on homepage</span>
    </div>`;
  list.appendChild(row);
  lucide.createIcons();
}

function removeProgramRow(btn) {
  btn.closest('.program-row').remove();
}

function saveCMSSettings() {
  const admissionsOpen   = document.getElementById('cmsAdmissionsToggle').classList.contains('on');
  const showAnnouncement = document.getElementById('cmsAnnouncementToggle').classList.contains('on');
  const heroTagline      = document.getElementById('cmsHeroTagline').value.trim();
  const deadline         = document.getElementById('cmsDeadline').value;
  const errorEl          = document.getElementById('cmsSaveError');
  const saveBtn          = document.getElementById('cmsSaveBtn');

  errorEl.classList.add('hidden');

  // Collect announcements
  const announcements = [];
  document.querySelectorAll('.announcement-row').forEach(row => {
    const text = row.querySelector('.ann-text').value.trim();
    const duration = parseInt(row.querySelector('.ann-duration').value) || 5;
    if (text) announcements.push({ text, duration: Math.max(3, duration) });
  });

  if (showAnnouncement && announcements.length === 0) {
    errorEl.textContent = 'Add at least one announcement, or turn off the announcement bar.';
    errorEl.classList.remove('hidden');
    return;
  }

  // Collect programs
  const programs = [];
  document.querySelectorAll('.program-row').forEach(row => {
    const name        = row.querySelector('.prog-name').value.trim();
    const degree      = row.querySelector('.prog-degree').value.trim();
    const description = row.querySelector('.prog-desc').value.trim();
    const visible     = row.querySelector('.prog-visible-toggle').classList.contains('on');
    if (name) programs.push({ name, degree, description, visible });
  });

  // Collect downloads
  const downloads = [];
  document.querySelectorAll('.download-row').forEach(row => {
    const name = row.querySelector('.dl-name')?.value || '';
    const url = row.querySelector('.dl-url')?.value || '';
    const file_type = row.querySelector('.dl-type')?.value || '';
    if (name && url) downloads.push({ name, url, file_type });
  });

  saveBtn.disabled = true;
  saveBtn.innerHTML = '<i data-lucide="loader" class="w-4 h-4 animate-spin"></i> Saving...';
  lucide.createIcons();

  fetch('/admin-panel/api/cms/update/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body: JSON.stringify({
      admissions_open:      admissionsOpen,
      show_announcement:    showAnnouncement,
      announcements,
      hero_tagline:         heroTagline,
      application_deadline: deadline || null,
      programs,
      downloads,
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showToast('Homepage settings saved!', 'success');
    } else {
      errorEl.textContent = data.message || 'Failed to save settings.';
      errorEl.classList.remove('hidden');
    }
  })
  .catch(() => {
    errorEl.textContent = 'Network error. Please try again.';
    errorEl.classList.remove('hidden');
  })
  .finally(() => {
    saveBtn.disabled = false;
    saveBtn.innerHTML = '<i data-lucide="save" class="w-4 h-4"></i> Save Homepage Settings';
    lucide.createIcons();
  });
}

/* ═══ DOWNLOADS MANAGEMENT ═══ */
document.addEventListener('DOMContentLoaded', () => {
  const uploadBtn = document.getElementById('uploadDownloadBtn');
  const fileInput = document.getElementById('downloadFileInput');

  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleDownloadUpload);
  }
});

function handleDownloadUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  const uploadBtn = document.getElementById('uploadDownloadBtn');
  const originalHTML = uploadBtn.innerHTML;
  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Uploading...';
  lucide.createIcons();

  fetch('/admin-panel/api/cms/upload-file/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken()
    },
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      addDownloadRow(data.data);
      showToast('File uploaded successfully!', 'success');
    } else {
      showToast('Error: ' + data.message, 'warn');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    showToast('Error uploading file. Please try again.', 'warn');
  })
  .finally(() => {
    uploadBtn.disabled = false;
    uploadBtn.innerHTML = originalHTML;
    event.target.value = '';
    lucide.createIcons();
  });
}

function addDownloadRow(fileData) {
  const list = document.getElementById('downloadsList');

  // Remove empty state message if it exists
  const emptyMsg = list.querySelector('p');
  if (emptyMsg) emptyMsg.remove();

  // Create hidden input to store download data
  const row = document.createElement('div');
  row.className = 'download-row border border-gray-100 rounded-lg p-3 bg-gray-50 flex items-center justify-between gap-3';
  row.innerHTML = `
    <div class="flex items-center gap-3 flex-1 min-w-0">
      <div class="w-8 h-8 rounded-md bg-red-100 flex items-center justify-center flex-shrink-0 text-xs font-bold text-red-700">
        ${fileData.file_type}
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-gray-800 truncate">${fileData.name}</p>
        <p class="text-xs text-gray-400 truncate">${fileData.url}</p>
      </div>
      <input type="hidden" class="dl-name" value="${fileData.name}">
      <input type="hidden" class="dl-url" value="${fileData.url}">
      <input type="hidden" class="dl-type" value="${fileData.file_type}">
    </div>
    <button type="button" onclick="removeDownloadRow(this)"
      class="w-7 h-7 flex items-center justify-center text-red-400 hover:text-red-600 hover:bg-red-100 rounded-lg transition flex-shrink-0">
      <i data-lucide="x" class="w-4 h-4"></i>
    </button>`;
  list.appendChild(row);
  lucide.createIcons();
}

function removeDownloadRow(btn) {
  btn.closest('.download-row').remove();
}

// CSRF token helper
function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
    document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='))?.split('=')[1] || '';
}

/* ═══ MISSING REQUIREMENTS NOTIFICATION FEATURE ═══ */

// Initialize requirements page when switched
function initRequirementsPage() {
  loadStudentsWithRequirements();
  loadRequirementTypes();
}

// Load students with missing requirements
async function loadStudentsWithRequirements() {
  try {
    const response = await fetch('/admin-panel/api/requirements/students/', {
      method: 'GET',
      headers: { 'X-CSRFToken': getCSRFToken() }
    });
    const data = await response.json();
    
    if (data.success) {
      renderMissingRequirements(data.data);
      updateRequirementStats(data.data);
    }
  } catch (error) {
    console.error('Error loading students with requirements:', error);
    document.getElementById('missingRequirementsList').innerHTML = 
      '<p class="text-gray-400 text-sm text-center py-8">Error loading data. Please refresh.</p>';
  }
}

// Render the list of students with missing requirements
function renderMissingRequirements(students) {
  const container = document.getElementById('missingRequirementsList');
  
  if (!students || students.length === 0) {
    container.innerHTML = '<p class="text-gray-400 text-sm text-center py-8">No students with missing requirements.</p>';
    return;
  }
  
  container.innerHTML = students.map(student => {
    const reqsHtml = student.requirements.map(req => `
      <div class="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
        <div class="flex items-center gap-2">
          <input type="checkbox" class="req-checkbox w-4 h-4 rounded border-gray-300 text-red-600 focus:ring-red-500" 
            data-student-id="${student.user_id}" data-requirement-id="${req.id}">
          <span class="text-sm text-gray-700">${req.requirement_name}</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 text-xs rounded-full ${getReqStatusClass(req.status)}">${req.status}</span>
          <button onclick="removeRequirement(${req.id})" class="text-gray-400 hover:text-red-600">
            <i data-lucide="trash-2" class="w-4 h-4"></i>
          </button>
        </div>
      </div>
    `).join('');
    
    return `
      <div class="border border-gray-100 rounded-xl p-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-xs font-bold text-red-700">
              ${getInitials(student.full_name)}
            </div>
            <div>
              <p class="text-sm font-semibold text-gray-800">${student.full_name}</p>
              <p class="text-xs text-gray-400">${student.email}</p>
            </div>
          </div>
          <span class="text-xs text-gray-400">${student.application_id || 'No App'}</span>
        </div>
        <div class="pl-13">
          ${reqsHtml}
        </div>
      </div>
    `;
  }).join('');
  
  lucide.createIcons();
}

// Get CSS class for requirement status
function getReqStatusClass(status) {
  const classes = {
    'pending': 'bg-yellow-50 text-yellow-700',
    'notified': 'bg-blue-50 text-blue-700',
    'submitted': 'bg-green-50 text-green-700',
    'waived': 'bg-gray-50 text-gray-700'
  };
  return classes[status] || 'bg-gray-50 text-gray-700';
}

// Update requirement statistics
function updateRequirementStats(students) {
  let total = 0, pending = 0, notified = 0, submitted = 0;
  
  students.forEach(student => {
    student.requirements.forEach(req => {
      total++;
      if (req.status === 'pending') pending++;
      else if (req.status === 'notified') notified++;
      else if (req.status === 'submitted') submitted++;
    });
  });
  
  document.getElementById('reqTotalCount').textContent = total;
  document.getElementById('reqPendingCount').textContent = pending;
  document.getElementById('reqNotifiedCount').textContent = notified;
  document.getElementById('reqSubmittedCount').textContent = submitted;
}

// Load requirement types for dropdowns
async function loadRequirementTypes() {
  try {
    const response = await fetch('/admin-panel/api/requirements/types/', {
      method: 'GET',
      headers: { 'X-CSRFToken': getCSRFToken() }
    });
    const data = await response.json();
    
    if (data.success) {
      populateRequirementDropdowns(data.data);
    }
  } catch (error) {
    console.error('Error loading requirement types:', error);
  }
}

// Populate requirement dropdowns
function populateRequirementDropdowns(types) {
  const select = document.getElementById('addReqRequirementSelect');
  select.innerHTML = '<option value="">-- Select a requirement --</option>' + 
    types.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
}

// Open add requirement modal
async function openAddRequirementModal() {
  // Load all students
  try {
    const response = await fetch('/admin-panel/api/students/all/', {
      method: 'GET',
      headers: { 'X-CSRFToken': getCSRFToken() }
    });
    const data = await response.json();
    
    if (data.success) {
      const select = document.getElementById('addReqStudentSelect');
      select.innerHTML = '<option value="">-- Select a student --</option>' + 
        data.data.map(s => `<option value="${s.user_id}">${s.full_name} (${s.email})</option>`).join('');
    }
  } catch (error) {
    console.error('Error loading students:', error);
  }
  
  // Load requirement types
  await loadRequirementTypes();
  
  // Clear form
  document.getElementById('addReqNotes').value = '';
  document.getElementById('addReqError').classList.add('hidden');
  
  // Show modal
  document.getElementById('addRequirementModal').style.display = 'flex';
}

function closeAddRequirementModal() {
  document.getElementById('addRequirementModal').style.display = 'none';
}

// Save student requirement
async function saveStudentRequirement() {
  const studentId = document.getElementById('addReqStudentSelect').value;
  const requirementId = document.getElementById('addReqRequirementSelect').value;
  const notes = document.getElementById('addReqNotes').value;
  const errorEl = document.getElementById('addReqError');
  
  if (!studentId || !requirementId) {
    errorEl.textContent = 'Please select both a student and a requirement.';
    errorEl.classList.remove('hidden');
    return;
  }
  
  errorEl.classList.add('hidden');
  
  try {
    const response = await fetch('/admin-panel/api/requirements/add/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: parseInt(studentId),
        requirement_id: parseInt(requirementId),
        notes: notes
      })
    });
    const data = await response.json();
    
    if (data.success) {
      showToast('Requirement added successfully!', 'success');
      closeAddRequirementModal();
      loadStudentsWithRequirements();
    } else {
      errorEl.textContent = data.message;
      errorEl.classList.remove('hidden');
    }
  } catch (error) {
    errorEl.textContent = 'An error occurred. Please try again.';
    errorEl.classList.remove('hidden');
  }
}

// Remove a student requirement
async function removeRequirement(requirementId) {
  if (!confirm('Are you sure you want to remove this requirement?')) return;
  
  try {
    const response = await fetch('/admin-panel/api/requirements/remove/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ student_requirement_id: requirementId })
    });
    const data = await response.json();
    
    if (data.success) {
      showToast('Requirement removed successfully!', 'success');
      loadStudentsWithRequirements();
    } else {
      showToast('Error: ' + data.message, 'warn');
    }
  } catch (error) {
    showToast('Error removing requirement.', 'warn');
  }
}

// Open manage requirements modal
async function openManageRequirementsModal() {
  await loadRequirementTypesForManagement();
  document.getElementById('manageRequirementsModal').style.display = 'flex';
}

function closeManageRequirementsModal() {
  document.getElementById('manageRequirementsModal').style.display = 'none';
}

// Load requirement types for management
async function loadRequirementTypesForManagement() {
  try {
    const response = await fetch('/admin-panel/api/requirements/types/', {
      method: 'GET',
      headers: { 'X-CSRFToken': getCSRFToken() }
    });
    const data = await response.json();
    
    if (data.success) {
      const container = document.getElementById('requirementTypesList');
      if (data.data.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm text-center py-4">No requirement types yet.</p>';
      } else {
        container.innerHTML = data.data.map(t => `
          <div class="flex items-center justify-between p-2 border border-gray-100 rounded-lg">
            <div>
              <p class="text-sm font-medium text-gray-800">${t.name}</p>
              <p class="text-xs text-gray-400">${t.description || ''}</p>
            </div>
            <button onclick="deleteRequirementType(${t.id})" class="text-gray-400 hover:text-red-600">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        `).join('');
        lucide.createIcons();
      }
    }
  } catch (error) {
    console.error('Error loading requirement types:', error);
  }
}

// Create new requirement type
async function createRequirementType() {
  const name = document.getElementById('newReqTypeName').value.trim();
  const errorEl = document.getElementById('manageReqError');
  
  if (!name) {
    errorEl.textContent = 'Please enter a requirement name.';
    errorEl.classList.remove('hidden');
    return;
  }
  
  errorEl.classList.add('hidden');
  
  try {
    const response = await fetch('/admin-panel/api/requirements/types/create/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name: name, description: '' })
    });
    const data = await response.json();
    
    if (data.success) {
      showToast('Requirement type created!', 'success');
      document.getElementById('newReqTypeName').value = '';
      await loadRequirementTypesForManagement();
      await loadRequirementTypes();
    } else {
      errorEl.textContent = data.message;
      errorEl.classList.remove('hidden');
    }
  } catch (error) {
    errorEl.textContent = 'An error occurred. Please try again.';
    errorEl.classList.remove('hidden');
  }
}

// Delete requirement type
async function deleteRequirementType(typeId) {
  if (!confirm('Are you sure you want to delete this requirement type?')) return;
  
  try {
    const response = await fetch('/admin-panel/api/requirements/types/delete/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ requirement_type_id: typeId })
    });
    const data = await response.json();
    
    if (data.success) {
      showToast('Requirement type deleted!', 'success');
      await loadRequirementTypesForManagement();
      await loadRequirementTypes();
    } else {
      showToast('Error: ' + data.message, 'warn');
    }
  } catch (error) {
    showToast('Error deleting requirement type.', 'warn');
  }
}

// Open notification modal
async function openNotifyModal() {
  // Load students with requirements
  try {
    const response = await fetch('/admin-panel/api/requirements/students/', {
      method: 'GET',
      headers: { 'X-CSRFToken': getCSRFToken() }
    });
    const data = await response.json();
    
    if (data.success) {
      const container = document.getElementById('notifyStudentList');
      if (data.data.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm text-center py-4">No students with missing requirements.</p>';
      } else {
        container.innerHTML = data.data.map(student => {
          const reqNames = student.requirements.map(r => r.requirement_name).join(', ');
          return `
            <div class="flex items-center gap-2 p-2 border border-gray-100 rounded-lg">
              <input type="checkbox" class="notify-checkbox w-4 h-4 rounded border-gray-300 text-red-600 focus:ring-red-500" 
                data-student-id="${student.user_id}" data-requirements="${student.requirements.map(r => r.id).join(',')}">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">${student.full_name}</p>
                <p class="text-xs text-gray-400">${reqNames}</p>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (error) {
    console.error('Error loading students:', error);
  }
  
  document.getElementById('notifyMessage').value = '';
  document.getElementById('notifyError').classList.add('hidden');
  document.getElementById('notifyModal').style.display = 'flex';
}

function closeNotifyModal() {
  document.getElementById('notifyModal').style.display = 'none';
}

// Send notifications to selected students
async function sendNotifications() {
  const checkboxes = document.querySelectorAll('.notify-checkbox:checked');
  const message = document.getElementById('notifyMessage').value.trim();
  const errorEl = document.getElementById('notifyError');
  
  if (checkboxes.length === 0) {
    errorEl.textContent = 'Please select at least one student.';
    errorEl.classList.remove('hidden');
    return;
  }
  
  if (!message) {
    errorEl.textContent = 'Please enter a notification message.';
    errorEl.classList.remove('hidden');
    return;
  }
  
  errorEl.classList.add('hidden');
  
  // Collect all requirement IDs
  const requirementIds = [];
  checkboxes.forEach(cb => {
    const reqIds = cb.dataset.requirements.split(',');
    requirementIds.push(...reqIds);
  });
  
  try {
    const response = await fetch('/admin-panel/api/requirements/notify/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        student_requirement_ids: requirementIds.map(id => parseInt(id)),
        message: message
      })
    });
    const data = await response.json();
    
    if (data.success) {
      showToast(data.message, 'success');
      closeNotifyModal();
      loadStudentsWithRequirements();
    } else {
      errorEl.textContent = data.message;
      errorEl.classList.remove('hidden');
    }
  } catch (error) {
    errorEl.textContent = 'An error occurred. Please try again.';
    errorEl.classList.remove('hidden');
  }
}

// Add requirements page to switchPage function
const originalSwitchPage = switchPage;
switchPage = function(pageId, el) {
  originalSwitchPage(pageId, el);
  if (pageId === 'requirements') {
    initRequirementsPage();
  }
};

// Add backdrop close for new modals
document.addEventListener('DOMContentLoaded', () => {
  const addReqModal = document.getElementById('addRequirementModal');
  const manageReqModal = document.getElementById('manageRequirementsModal');
  const notifyModal = document.getElementById('notifyModal');
  
  if (addReqModal) {
    addReqModal.addEventListener('click', function(e) {
      if (e.target === this) closeAddRequirementModal();
    });
  }
  if (manageReqModal) {
    manageReqModal.addEventListener('click', function(e) {
      if (e.target === this) closeManageRequirementsModal();
    });
  }
  if (notifyModal) {
    notifyModal.addEventListener('click', function(e) {
      if (e.target === this) closeNotifyModal();
    });
  }
});

/* ═══ TOGGLE STUDENT ACCOUNT STATUS ═══ */
var toggleStudentId = null;
var toggleStudentIsActive = null;

function openToggleStatusModal(userId, fullName, isActive, reason, changedBy, changedAt) {
  console.log('openToggleStatusModal called', userId, fullName, isActive);
  
  toggleStudentId = userId;
  toggleStudentIsActive = isActive;
  
  var modal = document.getElementById('toggleStatusModal');
  console.log('modal element:', modal);
  
  if (!modal) {
    alert('Error: toggleStatusModal not found in the page HTML.');
    return;
  }
  
  document.getElementById('toggleStatusSubtitle').innerText = fullName;
  
  if (isActive) {
    document.getElementById('toggleStatusIcon').className = 'w-10 h-10 rounded-xl flex items-center justify-center bg-red-100';
    document.getElementById('toggleStatusIcon').innerHTML = '<i data-lucide="user-x" class="w-5 h-5 text-red-600"></i>';
    document.getElementById('toggleStatusTitle').innerText = 'Deactivate Student Account';
    document.getElementById('currentStatusBar').className = 'flex items-center gap-3 p-3 rounded-xl border text-sm font-medium bg-green-50 border-green-200 text-green-700';
    document.getElementById('currentStatusBar').innerHTML = '<i data-lucide="check-circle" class="w-4 h-4"></i><span>Account is currently <strong>Active</strong></span>';
    document.getElementById('toggleActionLabel').innerHTML = 'This will <strong style="color:#dc2626">deactivate</strong> the student account.';
    document.getElementById('toggleStatusConfirmBtn').className = 'flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition bg-red-600 hover:bg-red-700';
    document.getElementById('toggleStatusConfirmBtn').innerHTML = '<i data-lucide="user-x" class="w-4 h-4"></i> Deactivate Account';
  } else {
    document.getElementById('toggleStatusIcon').className = 'w-10 h-10 rounded-xl flex items-center justify-center bg-green-100';
    document.getElementById('toggleStatusIcon').innerHTML = '<i data-lucide="user-check" class="w-5 h-5 text-green-600"></i>';
    document.getElementById('toggleStatusTitle').innerText = 'Activate Student Account';
    document.getElementById('currentStatusBar').className = 'flex items-center gap-3 p-3 rounded-xl border text-sm font-medium bg-red-50 border-red-200 text-red-700';
    document.getElementById('currentStatusBar').innerHTML = '<i data-lucide="x-circle" class="w-4 h-4"></i><span>Account is currently <strong>Inactive</strong></span>';
    document.getElementById('toggleActionLabel').innerHTML = 'This will <strong style="color:#16a34a">activate</strong> the student account.';
    document.getElementById('toggleStatusConfirmBtn').className = 'flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition bg-green-600 hover:bg-green-700';
    document.getElementById('toggleStatusConfirmBtn').innerHTML = '<i data-lucide="user-check" class="w-4 h-4"></i> Activate Account';
  }
  
  var lastNoteDiv = document.getElementById('lastStatusNote');
  if (reason) {
    lastNoteDiv.classList.remove('hidden');
    document.getElementById('lastStatusNoteText').innerText = reason;
    document.getElementById('lastStatusNoteBy').innerText = changedBy ? 'Changed by ' + changedBy : '';
  } else {
    lastNoteDiv.classList.add('hidden');
  }
  
  document.getElementById('toggleStatusReason').value = '';
  document.getElementById('toggleStatusReasonErr').classList.add('hidden');
  
  modal.style.display = 'flex';
  lucide.createIcons();
  console.log('Modal should be visible now');
}

function closeToggleStatusModal() {
  var modal = document.getElementById('toggleStatusModal');
  if (modal) modal.style.display = 'none';
  toggleStudentId = null;
  toggleStudentIsActive = null;
}

function confirmToggleStatus() {
  var reason = document.getElementById('toggleStatusReason').value.trim();
  var errorEl = document.getElementById('toggleStatusReasonErr');
  
  if (!reason) {
    errorEl.classList.remove('hidden');
    return;
  }
  
  errorEl.classList.add('hidden');
  
  fetch('/admin-panel/api/student/toggle-status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({user_id: toggleStudentId, is_active: !toggleStudentIsActive, reason: reason})
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.success) {
      showToast(data.message, 'success');
      closeToggleStatusModal();
      setTimeout(function() { location.reload(); }, 1000);
    } else {
      showToast('Error: ' + data.message, 'warn');
    }
  })
  .catch(function(e) { showToast('Error: ' + e.message, 'warn'); });
}


/* ═══ CURRICULUM FUNCTIONS ═══ */

// Toggle curriculum fields based on program level
function toggleCurriculumFields() {
  const level = document.getElementById('admProgramLevel')?.value;
  const container = document.getElementById('curriculumContainer');
  const doctoralFields = document.getElementById('doctoralFields');
  const otherProgramInput = document.getElementById('admDoctoralProgramOther');
  const programSelect = document.getElementById('admDoctoralProgram');

  if (!container) return;
  
  if (level === 'masters' || level === 'doctoral') {
    container.style.display = 'block';
    
    // Add an empty course row if no courses exist
    const tbody = document.getElementById('coursesTableBody');
    if (tbody && tbody.children.length === 0) {
      addCourseRow();
    }
    
    if (level === 'doctoral' && doctoralFields) {
      doctoralFields.style.display = 'block';
      if (programSelect && programSelect.value === 'Other' && otherProgramInput) {
        otherProgramInput.style.display = 'block';
      } else if (otherProgramInput) {
        otherProgramInput.style.display = 'none';
      }
    } else if (doctoralFields) {
      doctoralFields.style.display = 'none';
      if (otherProgramInput) otherProgramInput.style.display = 'none';
    }
  } else {
    container.style.display = 'none';
    if (doctoralFields) doctoralFields.style.display = 'none';
    if (otherProgramInput) otherProgramInput.style.display = 'none';
  }
}

// Add a new course row
function addCourseRow(courseData = null) {
  const tbody = document.getElementById('coursesTableBody');
  if (!tbody) return;
  
  const rowId = 'course_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4);

  const tr = document.createElement('tr');
  tr.className = 'border-b border-gray-100 hover:bg-gray-50';
  tr.id = rowId;

  const levelOptions = `
    <option value="1st Year 1st Sem">1st Year - 1st Sem</option>
    <option value="1st Year 2nd Sem">1st Year - 2nd Sem</option>
    <option value="2nd Year 1st Sem">2nd Year - 1st Sem</option>
    <option value="2nd Year 2nd Sem">2nd Year - 2nd Sem</option>
    <option value="3rd Year 1st Sem">3rd Year - 1st Sem</option>
    <option value="3rd Year 2nd Sem">3rd Year - 2nd Sem</option>
    <option value="Summer">Summer</option>
  `;

  tr.innerHTML = `
    <td class="px-2 py-2"><input type="text" class="course-code w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-red-300" placeholder="e.g., MIT 201" value="${courseData ? escapeHtml(courseData.code) : ''}"></td>
    <td class="px-2 py-2"><input type="text" class="course-title w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-red-300" placeholder="Subject title" value="${courseData ? escapeHtml(courseData.title) : ''}"></td>
    <td class="px-2 py-2 text-center"><input type="number" class="course-units w-16 text-center border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-red-300" value="${courseData ? courseData.units : '3'}" min="0" step="1" onchange="updateTotalUnits()"></td>
    <td class="px-2 py-2"><input type="text" class="course-prereq w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-red-300" placeholder="Pre-requisite" value="${courseData ? escapeHtml(courseData.prerequisite) : ''}"></td>
    <td class="px-2 py-2 text-center">
      <select class="course-level w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-red-300">
        ${levelOptions}
      </select>
    </td>
    <td class="px-2 py-2 text-center">
      <button type="button" onclick="removeCourseRow('${rowId}')" class="text-red-500 hover:text-red-700">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    </td>
  `;

  if (courseData && courseData.level) {
    const levelSelect = tr.querySelector('.course-level');
    if (levelSelect) levelSelect.value = courseData.level;
  }

  tbody.appendChild(tr);
  updateTotalUnits();
  updateCourseCount();
  if (typeof lucide !== 'undefined') lucide.createIcons();
}

function removeCourseRow(rowId) {
  const row = document.getElementById(rowId);
  if (row) {
    row.remove();
    updateTotalUnits();
    updateCourseCount();
  }
}

function updateTotalUnits() {
  let total = 0;
  document.querySelectorAll('.course-units').forEach(input => {
    const val = parseInt(input.value);
    if (!isNaN(val)) total += val;
  });
  const totalEl = document.getElementById('totalUnits');
  if (totalEl) totalEl.textContent = total;
}

function updateCourseCount() {
  const count = document.querySelectorAll('#coursesTableBody tr').length;
  const countEl = document.getElementById('courseCount');
  if (countEl) countEl.textContent = count;
}

function saveCurriculumData() {
  const courses = [];
  document.querySelectorAll('#coursesTableBody tr').forEach(row => {
    const code = row.querySelector('.course-code')?.value || '';
    const title = row.querySelector('.course-title')?.value || '';
    const units = parseInt(row.querySelector('.course-units')?.value) || 0;
    const prerequisite = row.querySelector('.course-prereq')?.value || '';
    const level = row.querySelector('.course-level')?.value || '';
    
    if (code && title && units > 0) {
      courses.push({ code, title, units, prerequisite, level });
    }
  });
  
  const programLevel = document.getElementById('admProgramLevel')?.value || '';
  let doctoralProgram = '';
  
  if (programLevel === 'doctoral') {
    const selectedProgram = document.getElementById('admDoctoralProgram')?.value || '';
    if (selectedProgram === 'Other') {
      doctoralProgram = document.getElementById('admDoctoralProgramOther')?.value || '';
    } else {
      doctoralProgram = selectedProgram;
    }
  }
  
  return {
    program_level: programLevel,
    doctoral_program: doctoralProgram,
    courses: courses,
    total_units: courses.reduce((sum, c) => sum + c.units, 0),
    course_count: courses.length
  };
}

function loadCurriculumData(savedData) {
  if (!savedData) return;
  
  const tbody = document.getElementById('coursesTableBody');
  if (tbody) tbody.innerHTML = '';
  
  const levelSelect = document.getElementById('admProgramLevel');
  if (levelSelect && savedData.program_level) {
    levelSelect.value = savedData.program_level;
    toggleCurriculumFields();
  }
  
  if (savedData.program_level === 'doctoral' && savedData.doctoral_program) {
    const programSelect = document.getElementById('admDoctoralProgram');
    const otherInput = document.getElementById('admDoctoralProgramOther');
    const predefinedPrograms = ['PhD in Educational Management', 'PhD in Public Administration', 'Doctor of Business Administration', 'Doctor of Information Technology'];
    
    if (predefinedPrograms.includes(savedData.doctoral_program)) {
      if (programSelect) programSelect.value = savedData.doctoral_program;
    } else {
      if (programSelect) programSelect.value = 'Other';
      if (otherInput) {
        otherInput.style.display = 'block';
        otherInput.value = savedData.doctoral_program;
      }
    }
  }
  
  if (savedData.courses && savedData.courses.length) {
    savedData.courses.forEach(course => addCourseRow(course));
  }
  
  updateTotalUnits();
  updateCourseCount();
}

// Modify the existing openModal function to include curriculum loading
// Find the existing openModal function in admin_scripts.js and replace it with this:
 function openModal(id) {
  console.log('openModal called with id:', id);
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) {
    console.error('Application not found with id:', id);
    alert('Error: Could not find application with ID ' + id);
    return;
  }
  document.getElementById("modalID").innerText = selectedApp.id;
  document.getElementById("mName").innerText = selectedApp.name;
  document.getElementById("mEmail").innerText = selectedApp.email;
  document.getElementById("mCourse").innerText = selectedApp.course;
  document.getElementById("mMobile").innerText = selectedApp.mobile;
  document.getElementById("mAppID").innerText = selectedApp.id;
  document.getElementById("mDate").innerText = selectedApp.submission_date;
  document.getElementById("lastUpdated").innerText = "Last updated: " + new Date().toISOString().split("T")[0];
  document.getElementById("remarks").value = selectedApp.remarks || "";
  
  renderDocCards();
  
  // Now populate admission dropdowns and set selected values
  populateAdmissionDetails();
  
  // Load curriculum data
  setTimeout(() => {
    const levelSelect = document.getElementById('admProgramLevel');
    if (levelSelect) {
      levelSelect.value = '';
      toggleCurriculumFields(); // ← let the function handle visibility
    }
  }, 100);
  
  const modal = document.getElementById("modal");
  if (modal) {
    modal.classList.add("open");
    modal.style.display = "flex";
  }
}

// Modify the existing markVerified function
function markVerified() {
  const curriculumData = saveCurriculumData();
  const remarks = document.getElementById("remarks").value;
  const semester = document.getElementById("admSemester")?.value || "";
  const yearAdmitted = document.getElementById("admYear")?.value || "";
  const programLevel = document.getElementById("admProgramLevel")?.value || "";

  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'verified',
      remarks: remarks,
      semester: semester,
      year_admitted: yearAdmitted,
      program_level: programLevel,
      curriculum_data: curriculumData
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      selectedApp.remarks = remarks;
      selectedApp.status = "Verified";
      selectedApp.semester = semester;
      selectedApp.year_admitted = yearAdmitted;
      selectedApp.program_level = programLevel;
      selectedApp.curriculum_data = curriculumData;
      showToast(selectedApp.id + " marked as Verified ✓");
      closeModal();
      initializeData();
      renderTable();
      renderDashboard();
    } else {
      showToast('Error: ' + data.message, 'error');
    }
  })
  .catch(e => { showToast('Error: ' + e.message, 'error'); });
}

// Add escapeHtml helper if not exists
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Add event listener for doctoral program change after DOM loads
document.addEventListener('DOMContentLoaded', function() {
  const programSelect = document.getElementById('admDoctoralProgram');
  if (programSelect) {
    programSelect.addEventListener('change', function() {
      const otherInput = document.getElementById('admDoctoralProgramOther');
      if (this.value === 'Other' && otherInput) {
        otherInput.style.display = 'block';
      } else if (otherInput) {
        otherInput.style.display = 'none';
      }
    });
  }
});


/* ═══ CURRICULUM TAB MANAGEMENT ═══ */
let currentCurriculumTab = 'program-info';

function switchCurriculumTab(tabId) {
  // Hide all tab contents
  document.querySelectorAll('.curriculum-tab-content').forEach(content => {
    content.classList.add('hidden');
  });
  
  // Show selected tab content
  const selectedContent = document.getElementById(`curriculum-tab-${tabId}`);
  if (selectedContent) {
    selectedContent.classList.remove('hidden');
  }
  
  // Update tab button styles
  document.querySelectorAll('.curriculum-tab').forEach(btn => {
    btn.classList.remove('bg-red-700', 'text-white');
    btn.classList.add('bg-gray-100', 'text-gray-600');
  });
  
  // Find and highlight the clicked tab
  const tabs = document.querySelectorAll('.curriculum-tab');
  let tabIndex = 0;
  if (tabId === 'program-info') tabIndex = 0;
  else if (tabId === 'courses') tabIndex = 1;
  else if (tabId === 'summary') tabIndex = 2;
  
  if (tabs[tabIndex]) {
    tabs[tabIndex].classList.remove('bg-gray-100', 'text-gray-600');
    tabs[tabIndex].classList.add('bg-red-700', 'text-white');
  }
  
  currentCurriculumTab = tabId;
  
  // If switching to summary tab, update the summary data
  if (tabId === 'summary') {
    updateCurriculumSummary();
  }
}

function updateCurriculumSummary() {
  let level11 = 0, level12 = 0, level21 = 0, level22 = 0, level31 = 0, level32 = 0, summer = 0;
  
  document.querySelectorAll('#coursesTableBody tr').forEach(row => {
    const units = parseInt(row.querySelector('.course-units')?.value) || 0;
    const level = row.querySelector('.course-level')?.value || '';
    
    switch(level) {
      case '1st Year 1st Sem': level11 += units; break;
      case '1st Year 2nd Sem': level12 += units; break;
      case '2nd Year 1st Sem': level21 += units; break;
      case '2nd Year 2nd Sem': level22 += units; break;
      case '3rd Year 1st Sem': level31 += units; break;
      case '3rd Year 2nd Sem': level32 += units; break;
      case 'Summer': summer += units; break;
    }
  });
  
  document.getElementById('level11Units').textContent = level11;
  document.getElementById('level12Units').textContent = level12;
  document.getElementById('level21Units').textContent = level21;
  document.getElementById('level22Units').textContent = level22;
  document.getElementById('level31Units').textContent = level31;
  document.getElementById('level32Units').textContent = level32;
  document.getElementById('summerUnits').textContent = summer;
}

function toggleDoctoralProgramOther() {
  const programSelect = document.getElementById('admDoctoralProgram');
  const otherInput = document.getElementById('admDoctoralProgramOther');
  if (programSelect && otherInput) {
    if (programSelect.value === 'Other') {
      otherInput.style.display = 'block';
    } else {
      otherInput.style.display = 'none';
    }
  }
}

function importSampleCurriculum() {
  if (!confirm('Load sample MIT curriculum? This will replace any existing courses.')) return;
  
  const tbody = document.getElementById('coursesTableBody');
  if (tbody) tbody.innerHTML = '';
  
  const sampleCourses = [
    { code: 'MIT 201', title: 'Advanced Programming', units: 3, prerequisite: 'None', level: '1st Year 1st Sem' },
    { code: 'MIT 202', title: 'Database Systems', units: 3, prerequisite: 'MIT 201', level: '1st Year 1st Sem' },
    { code: 'MIT 203', title: 'Research Methods', units: 3, prerequisite: 'None', level: '1st Year 1st Sem' },
    { code: 'MIT 204', title: 'Network Security', units: 3, prerequisite: 'MIT 201', level: '1st Year 2nd Sem' },
    { code: 'MIT 205', title: 'Software Engineering', units: 3, prerequisite: 'MIT 202', level: '1st Year 2nd Sem' },
    { code: 'MIT 206', title: 'Data Analytics', units: 3, prerequisite: 'MIT 202', level: '2nd Year 1st Sem' },
    { code: 'MIT 207', title: 'Thesis Writing', units: 6, prerequisite: 'MIT 203', level: '2nd Year 2nd Sem' },
  ];
  
  sampleCourses.forEach(course => addCourseRow(course));
  showToast('Sample curriculum loaded', 'success');
}

// Override the existing updateTotalUnits function to also update summary
const originalUpdateTotalUnits = updateTotalUnits;
updateTotalUnits = function() {
  if (originalUpdateTotalUnits) originalUpdateTotalUnits();
  updateCurriculumSummary();
};

// Override the existing updateCourseCount function
const originalUpdateCourseCount = updateCourseCount;
updateCourseCount = function() {
  if (originalUpdateCourseCount) originalUpdateCourseCount();
  updateCurriculumSummary();
};

// Override the existing toggleCurriculumFields function to show program info
const originalToggleCurriculumFields = toggleCurriculumFields;
toggleCurriculumFields = function() {
  if (originalToggleCurriculumFields) originalToggleCurriculumFields();
  
  const level = document.getElementById('admProgramLevel')?.value;
  
  if (level === 'masters') {
    document.getElementById('curriculumProgramName').value = 'Master in Information Technology';
    document.getElementById('curriculumDegreeCode').value = 'MIT';
  } else if (level === 'doctoral') {
    document.getElementById('curriculumProgramName').value = 'Doctoral Program';
    document.getElementById('curriculumDegreeCode').value = 'PhD';
  } else {
    document.getElementById('curriculumProgramName').value = '';
    document.getElementById('curriculumDegreeCode').value = '';
  }
  
  const container = document.getElementById('curriculumContainer');
  if (container && (level === 'masters' || level === 'doctoral')) {
    container.style.display = 'block';
    // Default to showing program-info tab
    switchCurriculumTab('program-info');
  } else if (container) {
    container.style.display = 'none';
  }
};

// Override the existing loadCurriculumData function
const originalLoadCurriculumData = loadCurriculumData;
loadCurriculumData = function(savedData) {
  if (originalLoadCurriculumData) originalLoadCurriculumData(savedData);
  
  // Set batch year if available
  if (savedData && savedData.batch_year) {
    document.getElementById('curriculumBatchYear').value = savedData.batch_year;
  }
  
  updateCurriculumSummary();
};

// Override the existing saveCurriculumData function
const originalSaveCurriculumData = saveCurriculumData;
saveCurriculumData = function() {
  const baseData = originalSaveCurriculumData ? originalSaveCurriculumData() : {};
  
  return {
    ...baseData,
    batch_year: document.getElementById('curriculumBatchYear')?.value || '',
    program_level: document.getElementById('admProgramLevel')?.value || '',
    doctoral_program: getDoctoralProgramValue(),
  };
};

function getDoctoralProgramValue() {
  const selectedProgram = document.getElementById('admDoctoralProgram')?.value || '';
  if (selectedProgram === 'Other') {
    return document.getElementById('admDoctoralProgramOther')?.value || '';
  }
  return selectedProgram;
}

function notifyMissingDoc(docType, docName) {
  if(!selectedApp) return;
  showToast(`Notification queued: ${docName} missing for ${selectedApp.name}`, 'warn');
  // TODO: wire to /admin-panel/api/requirements/notify/ with the student's user ID
  // and the relevant requirement, or send an email via a dedicated endpoint.
}

/* ═══ DOC VER TABS ═══ */
function switchDocVerTab(tab) {
  closeModal();          // close any open modal first
  document.querySelectorAll('.doc-ver-panel').forEach(p => p.classList.add('hidden'));
  document.querySelectorAll('.doc-ver-tab').forEach(b => {
    b.classList.remove('active', 'bg-white', 'text-red-800', 'shadow-sm');
    b.classList.add('text-gray-500');
  });

  const panel = document.getElementById('docVerPanel-' + tab);
  if (panel) panel.classList.remove('hidden');
  const btn = document.getElementById('docVerTab-' + tab);
  if (btn) {
    btn.classList.add('active', 'bg-white', 'text-red-800', 'shadow-sm');
    btn.classList.remove('text-gray-500');
  }

  // Always update the stat cards for whichever tab is active
  if (tab === 'application') { renderApplicationCards(); renderApplicationPanel(); }
  if (tab === 'admission')   { renderTable(); }          // updateCounts() is called inside renderTable
  if (tab === 'cor')         { typeof renderCORTable === 'function' && renderCORTable(); }
  if (tab === 'grades')      { typeof renderGradesTable === 'function' && renderGradesTable(); }

  lucide.createIcons();
}

function openApplicationTab(id) {
  initializeData();
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) { showToast('Application not found', 'error'); return; }
  renderApplicationCards();
  switchDocVerTab('application');
  renderApplicationPanel();
}

function renderApplicationCards() {
  const root = document.getElementById('applicationCards');
  const empty = document.getElementById('applicationEmpty');
  if (!root) return;
  root.innerHTML = '';
  updateApplicationStats();

  if (!applications || !applications.length) {
    if (empty) empty.classList.remove('hidden');
    return;
  }
  if (empty) empty.classList.add('hidden');

  applications.forEach(app => {
    const submittedDocs = (app.docs || []).filter(d => !d.missing).length;
    const totalDocs = (app.docs || []).length;

    root.insertAdjacentHTML('beforeend', `
      <div class="bg-white rounded-2xl shadow-sm p-5 fade-in hover:shadow-md transition cursor-pointer border border-gray-100 hover:border-gray-200"
           onclick="selectApplicationCard('${app.id}')">
        <div class="flex items-center gap-4 mb-3">
          <div class="w-12 h-12 rounded-full ${avatarBg(app.name || 'A')} flex items-center justify-center font-bold text-base flex-shrink-0">
            ${initials(app.name || '—')}
          </div>
          <div>
            <p class="font-bold text-gray-800 text-sm leading-tight">${escapeHtml(app.name || '—')}</p>
            <p class="text-xs text-gray-400">${escapeHtml(app.course || '—')} · ${escapeHtml(app.id || '—')}</p>
          </div>
        </div>
        <div class="mb-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Status</span>
            <div>${statusBadge(app.status || '')}</div>
          </div>
        </div>
        <div class="space-y-1.5 text-xs text-gray-500 mb-3">
          <p class="flex items-center gap-2"><i data-lucide="calendar" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>Submitted: ${escapeHtml(app.submission_date || '—')}</p>
          <p class="flex items-center gap-2"><i data-lucide="file-check" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>${submittedDocs}/${totalDocs} docs submitted</p>
        </div>
        <div class="border-t border-gray-100 pt-3 flex gap-2">
          <button onclick="event.stopPropagation(); verifyDocsForApp('${app.id}')"
            class="flex-1 flex items-center justify-center gap-1 text-xs font-semibold py-2 rounded-xl bg-gray-100 text-gray-700 hover:bg-gray-200 transition">
            <i data-lucide="file-text" class="w-3.5 h-3.5"></i> Verify Docs
          </button>
          <button onclick="event.stopPropagation(); verifyCORForApp('${app.id}')"
            class="flex-1 flex items-center justify-center gap-1 text-xs font-semibold py-2 rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 transition">
            <i data-lucide="receipt" class="w-3.5 h-3.5"></i> Verify COR
          </button>
          <button onclick="event.stopPropagation(); verifyGradesForApp('${app.id}')"
            class="flex-1 flex items-center justify-center gap-1 text-xs font-semibold py-2 rounded-xl bg-green-50 text-green-700 hover:bg-green-100 transition">
            <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i> Verify Grade
          </button>
        </div>
      </div>
    `);
  });
  lucide.createIcons();
}

function selectApplicationCard(id) {
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) return;
  openAppDetailsModal();
}

function openAppDetailsModal() {
  if (!selectedApp) return;
  const modal = document.getElementById('appDetailsModal');
  if (!modal) return;
  const reviewSections = document.getElementById('appModalReviewSections');
  
  // Populate modal with application data
  document.getElementById('appModalID').textContent = selectedApp.id || '—';
  document.getElementById('appModalSummaryID').textContent = selectedApp.id || '—';
  document.getElementById('appModalSummaryCourse').textContent = selectedApp.program_description || selectedApp.course || '—';
  document.getElementById('appModalSummaryDate').textContent = selectedApp.submission_date || '—';
  document.getElementById('appModalSummaryActivity').textContent = selectedApp.last_activity || '—';
  document.getElementById('appModalSummaryStatus').innerHTML = statusBadge(selectedApp.status || '');

  const personal = selectedApp.personal || {};
  const education = selectedApp.education || {};
  const working = selectedApp.working || {};
  const privacy = selectedApp.privacy || {};

  const fieldValue = (value, fallback = '—') => {
    if (value === null || value === undefined || value === '') return fallback;
    return escapeHtml(String(value));
  };

  const optionValue = (value, otherValue) => {
    if (!value) return '—';
    return value === 'Other' ? (otherValue || '—') : value;
  };

  const renderSection = (title, items) => {
    const rows = items
      .filter((item) => item[1] !== undefined && item[1] !== null && item[1] !== '')
      .map(([label, value]) => `
        <div class="border-b border-gray-100 pb-2 last:border-0">
          <span class="text-xs text-gray-400 uppercase tracking-wider">${escapeHtml(label)}</span>
          <p class="text-sm font-medium text-gray-800">${value}</p>
        </div>
      `)
      .join('');

    if (!rows) return '';

    return `
      <div class="review-section border border-gray-200 rounded-xl p-5 space-y-3 bg-white hover:shadow-md transition-all">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-bold text-brand" style="font-family:'Merriweather',serif">${escapeHtml(title)}</h3>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">${rows}</div>
      </div>
    `;
  };

  if (reviewSections) {
    reviewSections.innerHTML = [
      renderSection('Personal Details', [
        ['Full Name', fieldValue(personal.full_name || selectedApp.name)],
        ['Date of Birth', fieldValue(personal.dob)],
        ['Age', fieldValue(personal.age)],
        ['Gender', fieldValue(personal.gender)],
        ['Civil Status', fieldValue(personal.civil_status)],
        ['Place of Birth', fieldValue(personal.place_of_birth)],
        ['Religion', fieldValue(optionValue(personal.religion, personal.religion_other))],
        ['Ethnicity', fieldValue(optionValue(personal.ethnicity, personal.ethnicity_other))],
        ['Nationality', fieldValue(optionValue(personal.nationality, personal.nationality_other))],
        ['Disability', fieldValue(optionValue(personal.disability, personal.disability_other))],
        ['Permanent Address', fieldValue(personal.permanent_address)],
        ['Current Address', fieldValue(personal.current_address || personal.permanent_address)],
        ['Contact Number', fieldValue(personal.contact_number || selectedApp.mobile)],
        ['Email Address', fieldValue(personal.email || selectedApp.email)],
        ['Name of Parent', fieldValue(personal.name_of_parent)],
        ['Parent Relationship', fieldValue(personal.relationship)],
        ['Parent Monthly Income', fieldValue(personal.parent_income ? `₱${personal.parent_income}` : '')],
        ['Name of Spouse', fieldValue(personal.name_of_spouse)],
        ['Spouse Contact', fieldValue(personal.spouse_contact_number)],
        ['Spouse Monthly Income', fieldValue(personal.spouse_income ? `₱${personal.spouse_income}` : '')],
      ]),
      renderSection('Educational Background', [
        ['Elementary - School', fieldValue((education.elementary || {}).school_name)],
        ['Elementary - Degree', fieldValue((education.elementary || {}).degree_course)],
        ['Elementary - Year', fieldValue((education.elementary || {}).year_completed)],
        ['Secondary - School', fieldValue((education.secondary || {}).school_name)],
        ['Secondary - Degree', fieldValue((education.secondary || {}).degree_course)],
        ['Secondary - Year', fieldValue((education.secondary || {}).year_completed)],
        ['College - School', fieldValue((education.college || {}).school_name)],
        ['College - Degree', fieldValue((education.college || {}).degree_course)],
        ['College - Year', fieldValue((education.college || {}).year_completed)],
        ['Scholarship/Awards', fieldValue(education.scholarship || (education.college || {}).scholarship)],
        ['Graduate Studies - School', fieldValue((education.graduate || {}).school_name)],
        ['Graduate Studies - Degree', fieldValue((education.graduate || {}).degree_course)],
        ['Graduate Studies - Year', fieldValue((education.graduate || {}).year_completed)],
      ]),
      working.is_employed ? renderSection('Employment Information', [
        ['Position', fieldValue(working.position)],
        ['Monthly Income', fieldValue(working.monthly_income ? `₱${working.monthly_income}` : '')],
        ['Employment Status', fieldValue(optionValue(working.employment_status, working.employment_status_other))],
        ['Employer Name', fieldValue(working.employer_name)],
        ['Employer Address', fieldValue(working.employer_address)],
        ['Employer Contact', fieldValue(working.employer_contact)],
        ['Employer Classification', fieldValue(optionValue(working.employer_classification, working.employer_classification_other))],
      ]) : '',
      renderSection('Uploaded Documents', [
        ['MIT Curriculum', fieldValue((education.college || {}).mit_curriculum || (education.graduate || {}).mit_curriculum || 'Not selected')],
        ...(selectedApp.docs || []).map((doc) => [doc.name, fieldValue(doc.status === 'Missing' ? 'Missing' : `${doc.status}${doc.uploadDate ? ` · ${doc.uploadDate}` : ''}`)]),
      ]),
      privacy.agreed ? renderSection('Privacy Notice Consent', [
        ['Name', fieldValue(privacy.name || personal.full_name || selectedApp.name)],
        ['Date & Time', fieldValue(privacy.signed_at)],
        ['Consent Status', '✓ Agreed to Privacy Notice'],
        ['IP Address', fieldValue(privacy.ip_address || 'Collected upon submission')],
        ['Browser', fieldValue(privacy.user_agent ? privacy.user_agent.split(' ').slice(0, 3).join(' ') : '—')],
      ]) : '',
    ].filter(Boolean).join('');
  }
  
  // REMOVE OLD Program Details section (these lines can be removed since the Admission Details section now handles this)
  // document.getElementById('appModalPDLevel').textContent = (selectedApp.program_level || '—');
  // document.getElementById('appModalPDIntake').textContent = (selectedApp.semester || '—');
  // document.getElementById('appModalPDSpecialization').textContent = (selectedApp.specialization || '—');
  
  // ========== NEW: Populate Admission Details fields ==========
  // Populate semester dropdown
  const semesterSelect = document.getElementById('admSemester');
  if (semesterSelect) {
    semesterSelect.value = selectedApp.semester || '';
  }
  
  // Populate school year dropdown
  const yearSelect = document.getElementById('admYear');
  if (yearSelect) {
    yearSelect.value = selectedApp.year_admitted || '';
  }
  
  // Populate program level dropdown
  const programLevelSelect = document.getElementById('admProgramLevel');
  if (programLevelSelect) {
    programLevelSelect.value = selectedApp.program_level || '';
    // Trigger curriculum fields if program level is selected
    if (selectedApp.program_level) {
      toggleCurriculumFields();
    }
  }
  
  // Populate curriculum dropdown
  const curriculumSelect = document.getElementById('admCurriculum');
  if (curriculumSelect) {
    curriculumSelect.value = selectedApp.curriculum || '';
  }
  
  // Load curriculum data if exists
  if (selectedApp.curriculum_data) {
    loadCurriculumData(selectedApp.curriculum_data);
  }
  
  // Also populate the curriculum batch year if available in the data
  if (selectedApp.curriculum_data && selectedApp.curriculum_data.batch_year) {
    const batchYearInput = document.getElementById('curriculumBatchYear');
    if (batchYearInput) {
      batchYearInput.value = selectedApp.curriculum_data.batch_year;
    }
  }
  
  // Populate admission details fields (load dropdown options and set values)
  populateAdmissionDetails();
  
  modal.style.display = 'flex';
  modal.classList.add('fade-in');
  lucide.createIcons();
}

function closeAppDetailsModal() {
  const modal = document.getElementById('appDetailsModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('fade-in');
  }
}
function updateApplicationStats(){
  const s = applications.map(a=>(a.status||'').toLowerCase());
  document.getElementById("appTotalCount").innerText     =applications.length;
  document.getElementById("appPendingCount").innerText   =s.filter(x=>x==="pending review").length;
  document.getElementById("appReviewCount").innerText    =s.filter(x=>x==="under review").length;
  document.getElementById("appVerifiedCount").innerText  =s.filter(x=>x==="verified").length;
  document.getElementById("appIncompleteCount").innerText=s.filter(x=>x==="incomplete").length;
}

function _switchAndOpen(tabName, callback) {
  switchDocVerTab(tabName);
  // Wait one frame for the panel to become visible, then open modal
  requestAnimationFrame(() => {
    setTimeout(callback, 80);
  });
}

function verifyDocsForApp(id) {
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) return;
  // Switch to Admission Documents tab, then open the review modal
  _switchAndOpen('admission', () => openModal(id));
}
function verifyCORForApp(id) {
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) return;
  _switchAndOpen('cor', () => {
    // TODO: wire COR modal data fetch; for now only open the modal container
    // so UI flow is smooth.
    const m = document.getElementById('corModal');
    if (m) {
      m.classList.add('open');
      m.style.display = 'flex';
      // lightweight placeholder values
      document.getElementById('corModalStudentName')?.replaceChildren(document.createTextNode(selectedApp.name || '—'));
      lucide.createIcons();
    } else {
      showToast('COR modal not found', 'error');
    }
  });
}
function verifyGradesForApp(id) {
  selectedApp = applications.find(a => a.id === id);
  if (!selectedApp) return;

  // Switch to Grades tab first
  switchDocVerTab('grades');

  // Fetch all grade submissions, then find and open this student's
  fetch('/admin-panel/api/grade-submissions/', { credentials: 'same-origin' })
    .then(r => r.json())
    .then(data => {
      if (!data.success) { showToast('Error loading grades', 'error'); return; }
      gradesData = data.submissions || [];
      _updateGradeStats();
      _renderGradesRows();

      // Match by application ID (student_id field in submission)
      const submission = gradesData.find(g => g.student_id === selectedApp.id);
      if (submission) {
        requestAnimationFrame(() => setTimeout(() => openGradesModal(submission.id), 80));
      } else {
        showToast(`No grade submission found for ${selectedApp.name}`, 'warn');
      }
      lucide.createIcons();
    })
    .catch(e => showToast('Error: ' + e.message, 'error'));
}


function renderApplicationPanel(){
  const container = document.getElementById('docVerPanel-application');
  if(!container) return;
  const app = selectedApp || (applications.length? applications[0] : null);
  if(!app){
    container.querySelectorAll('span[id^="app"], span[id^="pi"], span[id^="ab"], span[id^="pd"]').forEach(el=>el.innerText='—');
    document.getElementById('requirementsList').innerHTML = '<div class="text-xs text-gray-400">Select an application from Admission Documents and click Details.</div>';
    document.getElementById('appProgressBar').style.width='0%';
    document.getElementById('timelineDates').innerText='';
    return;
  }
  // Summary
  document.getElementById('appID').innerText = app.id || '—';
  document.getElementById('appName').innerText = app.name || '—';
  document.getElementById('appCourse').innerText = app.course || '—';
  document.getElementById('appDate').innerText = app.submission_date || '—';
  document.getElementById('appStatus').innerHTML = statusBadge(app.status||'');

  // Personal info
  document.getElementById('piName').innerText = app.name || '—';
  document.getElementById('piDOB').innerText = app.dob || '—';
  document.getElementById('piAge').innerText = app.age || '—';
  document.getElementById('piGender').innerText = app.gender || '—';
  document.getElementById('piCitizenship').innerText = app.citizenship || '—';
  document.getElementById('piContact').innerText = app.mobile || '—';
  document.getElementById('piEmail').innerText = app.email || '—';
  document.getElementById('piAddress').innerText = app.address || '—';

  // Academic background
  document.getElementById('abSchool').innerText = (app.academic||{}).school || '—';
  document.getElementById('abYearGrad').innerText = (app.academic||{}).year_graduated || '—';
  document.getElementById('abDegree').innerText = (app.academic||{}).degree || '—';
  document.getElementById('abGWA').innerText = (app.academic||{}).gwa || '—';
  document.getElementById('abHonors').innerText = (app.academic||{}).honors || '—';

  // Program details
  document.getElementById('pdCourse').innerText = app.course || '—';
  document.getElementById('pdLevel').innerText = app.program_level || app.level || '—';
  document.getElementById('pdSpecialization').innerText = app.specialization || '—';
  document.getElementById('pdIntake').innerText = app.intake || '—';

  // Requirements checklist (expecting app.docs array)
  const reqRoot = document.getElementById('requirementsList');
  reqRoot.innerHTML = '';
  const docs = app.docs || [];
  // show first 6 docs or pad missing
  for(let i=0;i<6;i++){
    const d = docs[i] || {name: `Requirement ${i+1}`, status: 'Missing', uploadDate: ''};
    const status = d.status || (d.missing? 'Missing' : 'Pending Review');
    reqRoot.innerHTML += `
      <div class="p-3 border rounded-lg bg-white">
        <div class="flex items-center justify-between mb-1">
          <div class="text-sm font-medium text-gray-800">${escapeHtml(d.name)}</div>
          <div class="text-xs text-gray-500">${d.uploadDate||''}</div>
        </div>
        <div class="text-xs mt-1">${statusBadge(status)}</div>
      </div>`;
  }

  // Timeline: interpret app.status stages
  const stages = ['Submitted','Documents Verified','Under Review','Decision Made','Processed'];
  const idx = Math.max(0, stages.indexOf(app.status) );
  const pct = Math.min(100, Math.round(((idx+1)/stages.length)*100));
  document.getElementById('appProgressBar').style.width = pct + '%';
  const td = document.getElementById('timelineDates');
  td.innerHTML = stages.map((s,i)=>{
    const date = (app.timeline && app.timeline[s]) || (i===0 ? app.submission_date : '—');
    return `<div><strong class="text-gray-700">${escapeHtml(s)}:</strong> <span class="text-gray-500 text-xs">${escapeHtml(date||'—')}</span></div>`;
  }).join('');

  lucide.createIcons();
}

function _postDecision(decision){
  if(!selectedApp) { showToast('No application selected','error'); return; }
  if(!confirm(`Confirm ${decision} for application ${selectedApp.id}?`)) return;
  fetch('/admin-panel/api/application/decision/', {
    method: 'POST', credentials: 'same-origin', headers: {'Content-Type':'application/json','X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({ application_id: selectedApp.id, decision: decision })
  }).then(r=>r.json()).then(res=>{
    if(res.success){ showToast(res.message||'Updated'); selectedApp.status = decision; renderApplicationPanel(); renderTable(); }
    else showToast(res.message||'Unable to update','error');
  }).catch(err=>{ console.error(err); showToast('Network error','error'); });
}

function acceptApplication(){ _postDecision('Accepted'); }
function waitlistApplication(){ _postDecision('Waitlisted'); }
function rejectApplication(){ _postDecision('Rejected'); }


/* ═══ GRADES VERIFICATION ═══ */
let gradesData = [];
let selectedGrade = null;

function renderGradesTable() {
  const tbody = document.getElementById('gradesTableBody');
  if (!tbody) return;

  fetch('/admin-panel/api/grade-submissions/', { credentials: 'same-origin' })
    .then(r => r.json())
    .then(data => {
      if (!data.success) { showToast('Error loading grades', 'error'); return; }
      gradesData = data.submissions || [];
      _updateGradeStats();
      _renderGradesRows();
      lucide.createIcons();
    })
    .catch(e => showToast('Error: ' + e.message, 'error'));
}

function _updateGradeStats() {
  document.getElementById('gradesTotalCount').innerText       = gradesData.length;
  document.getElementById('gradesPendingCount').innerText     = gradesData.filter(g => g.status === 'Pending').length;
  document.getElementById('gradesAcknowledgedCount').innerText= gradesData.filter(g => g.status === 'Acknowledged').length;
  document.getElementById('gradesFlaggedCount').innerText     = gradesData.filter(g => g.status === 'Flagged').length;
}

function _renderGradesRows() {
  const tbody  = document.getElementById('gradesTableBody');
  const empty  = document.getElementById('gradesEmptyState');
  if (!tbody) return;

  const search       = (document.getElementById('gradesSearchInput')?.value || '').toLowerCase();
  const statusFilter = document.getElementById('gradesStatusFilter')?.value || 'all';
  const courseFilter = document.getElementById('gradesCourseFilter')?.value || 'all';

  const filtered = gradesData.filter(g => {
    const matchSearch = !search ||
      (g.student_name || '').toLowerCase().includes(search) ||
      (g.student_id   || '').toLowerCase().includes(search);
    const matchStatus = statusFilter === 'all' || g.status === statusFilter;
    const matchCourse = courseFilter === 'all' || (g.program || '').includes(courseFilter);
    return matchSearch && matchStatus && matchCourse;
  });

  tbody.innerHTML = '';

  if (!filtered.length) { empty?.classList.remove('hidden'); return; }
  empty?.classList.add('hidden');

  filtered.forEach(g => {
    const gpaNum     = g.gpa !== null ? parseFloat(g.gpa) : null;
    const gpaDisplay = gpaNum !== null ? gpaNum.toFixed(2) : '—';
    const gpaColor   = gpaNum !== null ? (gpaNum <= 2.0 ? 'text-green-600' : 'text-red-500') : 'text-gray-400';
    const screenshot = g.screenshot_url
      ? `<a href="${g.screenshot_url}" target="_blank"
           class="flex items-center gap-1 text-xs text-blue-600 hover:underline">
           <i data-lucide="image" class="w-3 h-3"></i> View
         </a>`
      : '<span class="text-xs text-gray-400">None</span>';

    tbody.innerHTML += `
      <tr class="hover:bg-gray-50/70 transition-colors">
        <td class="px-5 py-4">
          <p class="font-semibold text-gray-800 text-sm">${escapeHtml(g.student_name || '—')}</p>
          <p class="text-xs text-gray-400 font-mono">${escapeHtml(g.student_id || '—')}</p>
        </td>
        <td class="px-4 py-4 text-sm text-gray-700">${escapeHtml(g.program || '—')}</td>
        <td class="px-4 py-4 text-sm">
          <span class="font-medium text-gray-700">${escapeHtml(g.semester || '—')}</span>
          <span class="text-gray-400 text-xs block font-mono">${escapeHtml(g.school_year || '')}</span>
        </td>
        <td class="px-4 py-4 text-sm text-gray-600 font-mono">${g.subject_count} subject(s)</td>
        <td class="px-4 py-4">
          <span class="font-bold text-sm font-mono ${gpaColor}">${gpaDisplay}</span>
        </td>
        <td class="px-4 py-4">${screenshot}</td>
        <td class="px-4 py-4">${_gradeStatusBadge(g.status)}</td>
        <td class="px-4 py-4">
          <button onclick="openGradesModal(${g.id})"
            class="flex items-center gap-1.5 bg-green-50 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-green-100 transition">
            <i data-lucide="bar-chart-2" class="w-3.5 h-3.5"></i> Review
          </button>
        </td>
      </tr>`;
  });

  lucide.createIcons();
}

function _gradeStatusBadge(status) {
  const cls = {
    'Pending':      'bg-orange-100 text-orange-700',
    'Acknowledged': 'bg-green-100  text-green-700',
    'Flagged':      'bg-red-100    text-red-700',
  }[status] || 'bg-gray-100 text-gray-600';
  return `<span class="px-2 py-1 rounded-full text-xs font-semibold ${cls}">${escapeHtml(status || '—')}</span>`;
}

function openGradesModal(id) {
  selectedGrade = gradesData.find(g => g.id === id);
  if (!selectedGrade) return;

  document.getElementById('gradesModalStudentName').textContent = selectedGrade.student_name || '—';
  document.getElementById('gradesMName').textContent      = selectedGrade.student_name  || '—';
  document.getElementById('gradesMStudentID').textContent = selectedGrade.student_id    || '—';
  document.getElementById('gradesMProgram').textContent   = selectedGrade.program       || '—';
  document.getElementById('gradesMMSemester').textContent = selectedGrade.semester      || '—';
  document.getElementById('gradesMYear').textContent      = selectedGrade.school_year   || '—';

  const gpaNum = selectedGrade.gpa !== null ? parseFloat(selectedGrade.gpa) : null;
  const gpaEl  = document.getElementById('gradesMGPA');
  if (gpaEl) {
    gpaEl.textContent  = gpaNum !== null ? gpaNum.toFixed(2) : '—';
    gpaEl.className    = 'text-gray-800 font-bold ' + (gpaNum !== null ? (gpaNum <= 2.0 ? 'text-green-600' : 'text-red-500') : 'text-gray-400');
  }

  // Grade entries table
  const tbody = document.getElementById('gradesMTableBody');
  if (tbody) {
    if (!selectedGrade.grades?.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="px-4 py-6 text-center text-gray-400 text-sm">No grade entries available.</td></tr>`;
    } else {
      tbody.innerHTML = selectedGrade.grades.map(entry => {
        const g   = entry.grade !== null ? parseFloat(entry.grade) : null;
        const cls = g !== null ? (g <= 2.0 ? 'text-green-600 font-bold' : 'text-red-500 font-bold') : 'text-gray-400';
        return `<tr>
          <td class="px-4 py-3 text-xs font-mono font-semibold text-red-700">${escapeHtml(entry.code  || '—')}</td>
          <td class="px-4 py-3 text-xs text-gray-700">${escapeHtml(entry.title || '—')}</td>
          <td class="px-4 py-3 text-xs text-center font-mono text-gray-600">${entry.units ?? 0}</td>
          <td class="px-4 py-3 text-xs text-center font-mono ${cls}">${g !== null ? g.toFixed(2) : '—'}</td>
          <td class="px-4 py-3 text-xs text-center ${cls}">${g !== null ? (g <= 2.0 ? 'Passed' : 'Failed') : '—'}</td>
        </tr>`;
      }).join('');
    }
  }

  // Screenshot preview
  const preview = document.getElementById('gradesScreenshotPreview');
  if (preview) {
    preview.innerHTML = selectedGrade.screenshot_url
      ? `<img src="${selectedGrade.screenshot_url}" alt="Grade screenshot"
           class="max-w-full max-h-72 object-contain rounded-lg cursor-pointer shadow-sm"
           onclick="window.open('${selectedGrade.screenshot_url}','_blank')" />
         <p class="text-xs text-gray-400 mt-2 text-center">Click to open full size</p>`
      : `<i data-lucide="image" class="w-12 h-12 text-gray-300 mb-3"></i>
         <p class="text-sm text-gray-400">No screenshot uploaded yet.</p>`;
  }

  // Admin remarks
  document.getElementById('gradesRemarks').value = selectedGrade.admin_remarks || '';

  // Status badge
  const badge = document.getElementById('gradesCurrentStatusBadge');
  if (badge) {
    const cls = {
      'Pending':      'bg-orange-100 text-orange-700',
      'Acknowledged': 'bg-green-100  text-green-700',
      'Flagged':      'bg-red-100    text-red-700',
    }[selectedGrade.status] || 'bg-gray-100 text-gray-600';
    badge.className   = `px-3 py-1 rounded-full text-xs font-semibold ${cls}`;
    badge.textContent = selectedGrade.status || 'Pending';
  }

  const modal = document.getElementById('gradesModal');
  if (modal) { modal.classList.add('open'); modal.style.display = 'flex'; }
  lucide.createIcons();
}

function closeGradesModal() {
  const modal = document.getElementById('gradesModal');
  if (modal) { modal.classList.remove('open'); modal.style.display = 'none'; }
  selectedGrade = null;
}

function acknowledgeGrades() {
  if (!selectedGrade) return;
  _updateGradeStatus('Acknowledged', document.getElementById('gradesRemarks').value);
}

function flagGrades() {
  if (!selectedGrade) return;
  const remarks = document.getElementById('gradesRemarks').value.trim();
  if (!remarks) {
    showToast('Please add remarks before flagging.', 'warn');
    document.getElementById('gradesRemarks').focus();
    return;
  }
  _updateGradeStatus('Flagged', remarks);
}

function _updateGradeStatus(status, remarks) {
  fetch(`/admin-panel/api/grade-submissions/${selectedGrade.id}/update/`, {
    method:      'POST',
    credentials: 'same-origin',
    headers:     { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body:        JSON.stringify({ status, admin_remarks: remarks }),
  })
  .then(r => r.json())
  .then(data => {
    if (!data.success) { showToast('Error: ' + data.message, 'error'); return; }
    showToast(data.message, status === 'Flagged' ? 'warn' : 'success');
    const idx = gradesData.findIndex(g => g.id === selectedGrade.id);
    if (idx !== -1) {
      gradesData[idx].status        = status;
      gradesData[idx].admin_remarks = remarks;
    }
    closeGradesModal();
    _updateGradeStats();
    _renderGradesRows();
  })
  .catch(e => showToast('Error: ' + e.message, 'error'));
}

function exportGradesCSV() {
  const rows = [['Student Name', 'Student ID', 'Program', 'Semester', 'School Year', 'Subjects', 'GPA', 'Status']];
  gradesData.forEach(g => rows.push([
    g.student_name, g.student_id, g.program,
    g.semester, g.school_year, g.subject_count,
    g.gpa !== null ? parseFloat(g.gpa).toFixed(2) : '—',
    g.status,
  ]));
  const csv = rows.map(r => r.map(c => `"${String(c ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
  const a   = document.createElement('a');
  a.href    = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'grade_submissions.csv';
  a.click();
  showToast('Grades CSV exported');
}

// Live filters
document.getElementById('gradesSearchInput')?.addEventListener('input',  _renderGradesRows);
document.getElementById('gradesStatusFilter')?.addEventListener('change', _renderGradesRows);
document.getElementById('gradesCourseFilter')?.addEventListener('change', _renderGradesRows);

// Close on backdrop click
document.getElementById('gradesModal')?.addEventListener('click', function(e) {
  if (e.target === this) closeGradesModal();
});