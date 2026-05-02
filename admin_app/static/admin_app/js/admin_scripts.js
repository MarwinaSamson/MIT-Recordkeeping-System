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

// Initialize on page load
if(document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeData);
} else {
  initializeData();
}

// Document status summary function
function getDocStatus(docs){
  const v=docs.filter(d=>d.status==="Verified").length;
  const p=docs.filter(d=>d.status==="Pending Review"||d.status==="Under Review").length;
  const r=docs.filter(d=>d.status==="Rejected").length;
  let h="";
  if(v) h+=`<span class="flex items-center gap-1"><span class="dot dot-green"></span>${v} Verified</span>`;
  if(p) h+=`<span class="flex items-center gap-1"><span class="dot dot-orange"></span>${p} Pending</span>`;
  if(r) h+=`<span class="flex items-center gap-1"><span class="dot dot-red"></span>${r} Rejected</span>`;
  return h||`<span class="text-gray-400 text-xs">No docs</span>`;
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
function switchPage(pageId,el){
  // Ensure data is initialized from context
  initializeData();
  
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.getElementById('page-'+pageId).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  if(el) el.classList.add('active');
  if(pageId==='documents') renderTable();
  if(pageId==='students')  renderStudents();
  if(pageId==='history')   renderHistory();
  if(pageId==='dashboard') renderDashboard();
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
      tbody.innerHTML+=`
        <tr class="border-t border-gray-50 hover:bg-gray-50/70 transition-colors">
          <td class="px-5 py-4 text-red-700 font-semibold text-sm">${app.id}</td>
          <td class="px-4 py-4"><p class="font-semibold text-gray-800 text-sm">${app.name}</p><p class="text-xs text-gray-400">${app.email}</p><p class="text-xs text-gray-400">${app.mobile}</p></td>
          <td class="px-4 py-4 text-sm text-gray-700">${app.course}</td>
          <td class="px-4 py-4"><div class="flex flex-col gap-0.5 text-xs text-gray-600">${getDocStatus(app.docs)}</div></td>
          <td class="px-4 py-4">${statusBadge(app.status)}</td>
          <td class="px-4 py-4 text-xs text-gray-400">${app.last_activity}</td>
          <td class="px-4 py-4">
            <div class="flex items-center gap-2">
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
  grid.innerHTML=filtered.map(app=>`
    <div class="bg-white rounded-2xl shadow-sm p-5 fade-in hover:shadow-md transition">
      <div class="flex items-center gap-4 mb-4">
        <div class="w-12 h-12 rounded-full ${avatarBg(app.name)} flex items-center justify-center font-bold text-base flex-shrink-0">${initials(app.name)}</div>
        <div>
          <p class="font-bold text-gray-800 text-sm leading-tight">${app.name}</p>
          <p class="text-xs text-gray-400">${app.course} · ${app.id}</p>
        </div>
      </div>
      <div class="space-y-1.5 text-xs text-gray-500 mb-4">
        <p class="flex items-center gap-2"><i data-lucide="mail" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>${app.email}</p>
        <p class="flex items-center gap-2"><i data-lucide="phone" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>${app.mobile}</p>
        <p class="flex items-center gap-2"><i data-lucide="calendar" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>Submitted: ${app.submission_date}</p>
      </div>
      <div class="border-t border-gray-100 pt-3 flex items-center justify-between">
        ${statusBadge(app.status)}
        <button onclick="switchPage('documents',document.querySelectorAll('.nav-item')[1]);setTimeout(()=>openModal('${app.id}'),120)"
          class="text-xs text-red-700 font-semibold hover:underline flex items-center gap-1"><i data-lucide="eye" class="w-3 h-3"></i> View Docs</button>
      </div>
    </div>`).join("");
  lucide.createIcons();
}

/* ═══ HISTORY ═══ */
function renderHistory(){
  const tbody=document.getElementById("historyBody");
  if(!tbody) return;
  const search=(document.getElementById("historySearch")?.value||"").toLowerCase();
  const filter=document.getElementById("historyFilter")?.value||"all";
  let filtered=activityLog.filter(l=>
    (l.appId.toLowerCase().includes(search)||l.doc.toLowerCase().includes(search)||l.admin.toLowerCase().includes(search)||l.action.toLowerCase().includes(search))&&
    (filter==="all"||l.action===filter)
  );
  const ac={
    "Verified Document":"badge-verified",
    "Rejected Document":"badge-rejected",
    "Marked Incomplete":"badge-incomplete",
    "Requested Resubmission":"badge-pending",
    "Updated Profile":"badge-review",
    "Changed Profile Photo":"badge-review"
  };
  tbody.innerHTML=filtered.length
    ? filtered.map(l=>`
        <tr class="border-t border-gray-50 hover:bg-gray-50/70 transition-colors">
          <td class="px-5 py-3.5 text-xs text-gray-400 whitespace-nowrap">${l.time}</td>
          <td class="px-4 py-3.5 text-sm font-medium text-gray-700">${l.admin}</td>
          <td class="px-4 py-3.5 text-sm text-red-700 font-semibold">${l.appId}</td>
          <td class="px-4 py-3.5 text-sm text-gray-600">${l.doc}</td>
          <td class="px-4 py-3.5"><span class="status-badge ${ac[l.action]||'badge-review'}">${l.action}</span></td>
          <td class="px-4 py-3.5 text-xs text-gray-400">${l.notes}</td>
        </tr>`).join("")
    : `<tr><td colspan="6" class="px-5 py-12 text-center text-gray-400 text-sm">No activity logs found.</td></tr>`;
  lucide.createIcons();
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
  const currEl = document.getElementById("admCurriculum");
  if(semEl) semEl.value   = selectedApp.semester   || "";
  if(yearEl) yearEl.value = selectedApp.year_admitted || "";
  if(currEl) currEl.value = selectedApp.curriculum  || "";
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
  docPreviewCurrentIdx = (docPreviewCurrentIdx + dir + total) % total;
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
  const container=document.getElementById("docCards");
  container.innerHTML="";
  
  if(!selectedApp.docs || selectedApp.docs.length === 0){
    container.innerHTML=`<div class="col-span-full py-10 text-center text-gray-400"><i data-lucide="inbox" class="w-8 h-8 mx-auto mb-2 opacity-40"></i><p class="text-sm">No documents submitted yet.</p></div>`;
    lucide.createIcons(); return;
  }
  
  selectedApp.docs.forEach((doc, idx)=>{
    doc._idx = idx; // stash index for preview nav
    const isV=doc.status==="Verified", isR=doc.status==="Rejected";
    const border=isV?"border-green-300 bg-green-50/30":isR?"border-red-300 bg-red-50/30":"border-orange-200 bg-orange-50/20";
    const badge=isV
      ?`<span class="status-badge badge-verified"><i data-lucide="check-circle" class="w-3 h-3"></i>Verified</span>`
      :isR
      ?`<span class="status-badge badge-rejected"><i data-lucide="x-circle" class="w-3 h-3"></i>Rejected</span>`
      :`<span class="status-badge badge-review"><i data-lucide="clock" class="w-3 h-3"></i>${doc.status}</span>`;
    const issues=doc.issues&&doc.issues.length
      ?`<div class="mt-1.5 px-2 py-1.5 bg-red-50 rounded-lg"><p class="text-[11px] font-semibold text-red-500 mb-0.5">Issues:</p>${doc.issues.map(i=>`<p class="text-[11px] text-red-500 flex items-start gap-1"><span>•</span>${i}</p>`).join("")}</div>`:"";
    const verInfo=isV&&doc.verifiedBy
      ?`<p class="text-[11px] text-green-600 mt-1 flex items-center gap-1"><i data-lucide="user-check" class="w-3 h-3"></i>${doc.verifiedBy} · ${doc.verifiedOn}</p>`:"";
    const btns=!isV&&!isR
      ?`<div class="flex gap-2 mt-3">
          <button onclick="verifyDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white text-xs font-semibold py-2 rounded-xl hover:bg-green-600 transition shadow-sm"><i data-lucide="check" class="w-3 h-3"></i> Verify</button>
          <button onclick="rejectDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-red-500 text-white text-xs font-semibold py-2 rounded-xl hover:bg-red-600 transition shadow-sm"><i data-lucide="x" class="w-3 h-3"></i> Reject</button>
        </div>`
      :`<button onclick="unsetDoc(${idx})" class="w-full mt-3 text-xs text-gray-500 border border-gray-200 rounded-xl py-2 hover:bg-gray-50 transition">${isV?"↩ Undo Verify":"↩ Undo Reject"}</button>`;

    // Thumbnail label overlay for PDF
    const ext = getFileExt(doc.fileUrl||'');
    const isPdf = ext==='pdf';
    const previewLabel = isPdf
      ? `<span style="position:absolute;top:6px;left:6px;background:rgba(239,68,68,0.9);color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:4px;letter-spacing:.04em">PDF</span>`
      : '';

    container.innerHTML+=`
      <div class="doc-card border-2 ${border} rounded-2xl p-4 flex flex-col text-sm transition-shadow">
        <!-- Doc name + badge -->
        <div class="flex items-start justify-between gap-2 mb-3">
          <p class="font-semibold text-gray-800 text-xs leading-snug flex-1">${doc.name}</p>
          ${badge}
        </div>
        <!-- Clickable thumbnail preview -->
        <div class="relative rounded-xl overflow-hidden mb-3 cursor-pointer group" style="height:140px;background:#f3f4f6"
          onclick="openDocPreview(${idx})">
          ${getDocumentPreviewMarkup(doc, 'thumb')}
          ${previewLabel}
          <!-- hover overlay -->
          <div style="position:absolute;inset:0;background:rgba(0,0,0,0);transition:background .2s;display:flex;align-items:center;justify-content:center"
            class="group-hover:bg-black/20">
            <span style="opacity:0;transition:opacity .2s;background:rgba(0,0,0,0.65);color:#fff;font-size:11px;font-weight:600;padding:5px 12px;border-radius:8px;display:flex;align-items:center;gap:5px"
              class="group-hover:opacity-100">
              <i data-lucide="maximize-2" style="width:12px;height:12px"></i> Preview
            </span>
          </div>
        </div>
        <!-- Meta -->
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