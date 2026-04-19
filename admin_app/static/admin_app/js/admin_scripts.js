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

function renderDocCards(){
  const container=document.getElementById("docCards");
  container.innerHTML="";
  
  // If no docs array in data, just leave empty (don't alter design)
  if(!selectedApp.docs || selectedApp.docs.length === 0) {
    return;
  }
  
  selectedApp.docs.forEach((doc,idx)=>{
    const isV=doc.status==="Verified",isR=doc.status==="Rejected";
    const border=isV?"border-green-200":isR?"border-red-200":"border-orange-200";
    const badge=isV
      ?`<span class="status-badge badge-verified"><i data-lucide="check-circle" class="w-3 h-3"></i>Verified</span>`
      :isR
      ?`<span class="status-badge badge-rejected"><i data-lucide="x-circle" class="w-3 h-3"></i>Rejected</span>`
      :`<span class="status-badge badge-review"><i data-lucide="clock" class="w-3 h-3"></i>${doc.status}</span>`;
    const issues=doc.issues.length?`<div class="mt-2"><p class="text-xs font-semibold text-red-500 mb-1">Issues:</p>${doc.issues.map(i=>`<p class="text-xs text-red-500 flex items-start gap-1"><span>•</span>${i}</p>`).join("")}</div>`:"";
    const verInfo=isV&&doc.verifiedBy?`<p class="text-xs text-gray-400 mt-1">Verified by: ${doc.verifiedBy}</p><p class="text-xs text-gray-400">Verified on: ${doc.verifiedOn}</p>`:"";
    const btns=!isV&&!isR
      ?`<div class="flex gap-2 mt-3">
          <button onclick="verifyDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white text-xs font-semibold py-1.5 rounded-lg hover:bg-green-600 transition"><i data-lucide="check" class="w-3 h-3"></i> Verify</button>
          <button onclick="rejectDoc(${idx})" class="flex-1 flex items-center justify-center gap-1 bg-red-500 text-white text-xs font-semibold py-1.5 rounded-lg hover:bg-red-600 transition"><i data-lucide="x" class="w-3 h-3"></i> Reject</button>
        </div>`
      :`<button onclick="unsetDoc(${idx})" class="w-full mt-3 text-xs text-gray-500 border border-gray-200 rounded-lg py-1.5 hover:bg-gray-50 transition">${isV?"Undo Verify":"Undo Reject"}</button>`;
    container.innerHTML+=`
      <div class="doc-card border-2 ${border} rounded-xl p-4 flex flex-col text-sm">
        <div class="flex items-center justify-between mb-3"><p class="font-semibold text-gray-800 text-xs leading-tight">${doc.name}</p>${badge}</div>
        <div class="flex-1 bg-gray-100 rounded-lg flex items-center justify-center h-24 mb-3">
          <div class="text-center text-gray-400"><i data-lucide="file-text" class="w-8 h-8 mx-auto mb-1 opacity-50"></i><p class="text-xs opacity-60">Document Preview</p></div>
        </div>
        <p class="text-xs text-gray-500"><span class="font-semibold">Type:</span> ${doc.type}</p>
        <p class="text-xs text-gray-500"><span class="font-semibold">Uploaded:</span> ${doc.uploadDate}</p>
        ${verInfo}${issues}${btns}
        <button onclick="viewFullDoc('${doc.fileUrl}', '${doc.name}')" class="mt-2 w-full flex items-center justify-center gap-1 border border-gray-200 text-gray-600 text-xs py-1.5 rounded-lg hover:bg-gray-50 transition"><i data-lucide="eye" class="w-3 h-3"></i> View Full</button>
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
      doc.verifiedBy="Marwina Admin";
      doc.verifiedOn=new Date().toISOString().split("T")[0];
      doc.issues=[];
      showToast(data.message);
      renderDocCards();
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
    } else {
      showToast('Error: '+data.message,'error');
    }
  })
  .catch(e=>{showToast('Error: '+e.message,'error');});
}

/* ═══ MODAL ACTIONS ═══ */
function markVerified(){
  const remarks=document.getElementById("remarks").value;
  
  fetch('/admin-panel/api/application/status/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken()},
    body: JSON.stringify({
      application_id: selectedApp.id,
      status: 'verified',
      remarks: remarks
    })
  })
  .then(r=>r.json())
  .then(data=>{
    if(data.success){
      selectedApp.remarks=remarks;
      selectedApp.status="Verified";
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
function handleLogout(){if(confirm("Log out of the admin panel?")) showToast("Logged out successfully");}

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