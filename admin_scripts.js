lucide.createIcons();


let applications = [
  {id:"MIT-0001",name:"Noellene Pearl A. Villarcampo",course:"MIT",email:"villarcamponoellenepearl@gmail.com",mobile:"+639610056461",submissionDate:"2026-02-21",lastActivity:"21/02/2026",status:"Under Review",remarks:"",
    docs:[
      {name:"Admission Form",       type:"Academic Form",status:"Verified",     uploadDate:"2026-02-21",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-21",issues:[]},
      {name:"Transcript of Records",type:"Academic Form",status:"Under Review",  uploadDate:"2026-02-21",verifiedBy:"",verifiedOn:"",issues:["Document appears blurry","Please upload higher resolution"]},
      {name:"Recommendation Letter",type:"Academic Form",status:"Rejected",      uploadDate:"2026-02-21",verifiedBy:"",verifiedOn:"",issues:["Document is blurry"]},
    ]},
  {id:"MIT-0002",name:"Juan Dela Cruz",course:"MIT",email:"juan.delacruz@gmail.com",mobile:"+639171234567",submissionDate:"2026-02-20",lastActivity:"21/02/2026",status:"Verified",remarks:"",
    docs:[
      {name:"Admission Form",      type:"Academic Form",status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Transcript",          type:"Academic Form",status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Birth Certificate",   type:"Legal Doc",    status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Diploma",             type:"Academic Form",status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Medical Certificate", type:"Medical Doc",  status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Recommendation 1",    type:"Academic Form",status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
      {name:"Proof of Payment",    type:"Financial Doc",status:"Verified",uploadDate:"2026-02-20",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-20",issues:[]},
    ]},
  {id:"MIT-0003",name:"Maria Santos",course:"MIT",email:"maria.santos@gmail.com",mobile:"+639189876543",submissionDate:"2026-02-19",lastActivity:"21/02/2026",status:"Pending Review",remarks:"",
    docs:[
      {name:"Admission Form",  type:"Academic Form",status:"Verified",      uploadDate:"2026-02-19",verifiedBy:"",verifiedOn:"",issues:[]},
      {name:"Transcript",      type:"Academic Form",status:"Pending Review", uploadDate:"2026-02-19",verifiedBy:"",verifiedOn:"",issues:[]},
      {name:"Recommendation",  type:"Academic Form",status:"Rejected",       uploadDate:"2026-02-19",verifiedBy:"",verifiedOn:"",issues:["Signature missing"]},
    ]},
  {id:"MIT-0004",name:"Pedro Reyes",course:"MIT",email:"pedro.reyes@gmail.com",mobile:"+639201112222",submissionDate:"2026-02-18",lastActivity:"21/02/2026",status:"Incomplete",remarks:"",
    docs:[
      {name:"Admission Form",type:"Academic Form",status:"Verified",    uploadDate:"2026-02-18",verifiedBy:"Marwina Admin",verifiedOn:"2026-02-18",issues:[]},
      {name:"Transcript",    type:"Academic Form",status:"Under Review",uploadDate:"2026-02-18",verifiedBy:"",verifiedOn:"",issues:["Poor scan quality"]},
      {name:"Birth Cert",    type:"Legal Doc",    status:"Under Review",uploadDate:"2026-02-18",verifiedBy:"",verifiedOn:"",issues:["Document is blurry"]},
    ]},
];

let activityLog = [
  {time:"2026-02-21 10:32",admin:"Marwina Admin",appId:"MIT-0001",doc:"Admission Form",      action:"Verified",    notes:"Clear and complete."},
  {time:"2026-02-21 10:35",admin:"Marwina Admin",appId:"MIT-0001",doc:"Recommendation Letter",action:"Rejected",    notes:"Document is blurry."},
  {time:"2026-02-20 14:12",admin:"Marwina Admin",appId:"MIT-0002",doc:"All Documents",        action:"Verified",    notes:"All documents passed."},
  {time:"2026-02-19 09:00",admin:"Marwina Admin",appId:"MIT-0003",doc:"Recommendation",       action:"Rejected",    notes:"Signature missing."},
  {time:"2026-02-18 11:20",admin:"Marwina Admin",appId:"MIT-0004",doc:"Application",          action:"Incomplete",  notes:"Missing transcript."},
  {time:"2026-02-17 16:45",admin:"Marwina Admin",appId:"MIT-0003",doc:"Transcript",           action:"Resubmission",notes:"Requested clearer copy."},
];

let selectedApp=null, rejectTargetIdx=null, toastTimer=null;

/* ═══ NAV ═══ */
function switchPage(pageId,el){
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

/* ═══ HELPERS ═══ */
function docSummary(docs){
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
  const m={"Pending Review":"badge-pending","Under Review":"badge-review","Verified":"badge-verified","Incomplete":"badge-incomplete","Rejected":"badge-rejected"};
  const ic={"Pending Review":"⏳","Under Review":"🔄","Verified":"✅","Incomplete":"⚠️","Rejected":"❌"};
  return `<span class="status-badge ${m[s]||'badge-review'}">${ic[s]||''}${s}</span>`;
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

/* ═══ DASHBOARD ═══ */
function renderDashboard(){
  const list=document.getElementById("dashRecentList");
  if(!list) return;
  list.innerHTML=applications.slice(0,4).map(a=>`
    <div class="flex items-center gap-4 p-3 rounded-xl hover:bg-gray-50 transition cursor-pointer" onclick="switchPage('documents',document.querySelectorAll('.nav-item')[1]);setTimeout(()=>openModal('${a.id}'),120)">
      <div class="w-9 h-9 rounded-full ${avatarBg(a.name)} flex items-center justify-center font-bold text-sm flex-shrink-0">${initials(a.name)}</div>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-semibold text-gray-800 truncate">${a.name}</p>
        <p class="text-xs text-gray-400">${a.course} · ${a.id}</p>
      </div>
      ${statusBadge(a.status)}
    </div>`).join("");

  const prog=document.getElementById("dashProgress");
  const total=applications.length||1;
  const stats=[
    {label:"Verified",   count:applications.filter(a=>a.status==="Verified").length,   color:"bg-green-400"},
    {label:"Under Review",count:applications.filter(a=>a.status==="Under Review").length,color:"bg-yellow-400"},
    {label:"Pending",    count:applications.filter(a=>a.status==="Pending Review").length,color:"bg-orange-400"},
    {label:"Incomplete", count:applications.filter(a=>a.status==="Incomplete").length,  color:"bg-red-400"},
  ];
  prog.innerHTML=stats.map(s=>`
    <div>
      <div class="flex justify-between text-xs mb-1"><span class="text-gray-500">${s.label}</span><span class="font-semibold text-gray-700">${Math.round(s.count/total*100)}%</span></div>
      <div class="prog-bar"><div class="prog-fill ${s.color}" style="width:${Math.round(s.count/total*100)}%"></div></div>
    </div>`).join("");
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
          <td class="px-4 py-4"><div class="flex flex-col gap-0.5 text-xs text-gray-600">${docSummary(app.docs)}</div></td>
          <td class="px-4 py-4">${statusBadge(app.status)}</td>
          <td class="px-4 py-4 text-xs text-gray-400">${app.lastActivity}</td>
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
  document.getElementById("totalCount").innerText     =applications.length;
  document.getElementById("pendingCount").innerText   =applications.filter(a=>a.status==="Pending Review").length;
  document.getElementById("reviewCount").innerText    =applications.filter(a=>a.status==="Under Review").length;
  document.getElementById("verifiedCount").innerText  =applications.filter(a=>a.status==="Verified").length;
  document.getElementById("incompleteCount").innerText=applications.filter(a=>a.status==="Incomplete").length;
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
        <p class="flex items-center gap-2"><i data-lucide="calendar" class="w-3.5 h-3.5 text-gray-400 flex-shrink-0"></i>Submitted: ${app.submissionDate}</p>
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
    (l.appId.toLowerCase().includes(search)||l.doc.toLowerCase().includes(search)||l.admin.toLowerCase().includes(search))&&
    (filter==="all"||l.action===filter)
  );
  const ac={"Verified":"badge-verified","Rejected":"badge-rejected","Incomplete":"badge-incomplete","Resubmission":"badge-pending"};
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
  selectedApp=applications.find(a=>a.id===id);
  if(!selectedApp) return;
  document.getElementById("modalID").innerText =selectedApp.id;
  document.getElementById("mName").innerText   =selectedApp.name;
  document.getElementById("mEmail").innerText  =selectedApp.email;
  document.getElementById("mCourse").innerText =selectedApp.course;
  document.getElementById("mMobile").innerText =selectedApp.mobile;
  document.getElementById("mAppID").innerText  =selectedApp.id;
  document.getElementById("mDate").innerText   =selectedApp.submissionDate;
  document.getElementById("lastUpdated").innerText="Last updated: "+new Date().toISOString().split("T")[0];
  document.getElementById("remarks").value     =selectedApp.remarks||"";
  renderDocCards();
  document.getElementById("modal").classList.add("open");
}
function closeModal(){document.getElementById("modal").classList.remove("open");}

function renderDocCards(){
  const container=document.getElementById("docCards");
  container.innerHTML="";
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
        <button onclick="viewFullDoc('${doc.name}')" class="mt-2 w-full flex items-center justify-center gap-1 border border-gray-200 text-gray-600 text-xs py-1.5 rounded-lg hover:bg-gray-50 transition"><i data-lucide="eye" class="w-3 h-3"></i> View Full</button>
      </div>`;
  });
  lucide.createIcons();
}

function verifyDoc(idx){
  selectedApp.docs[idx].status="Verified";
  selectedApp.docs[idx].verifiedBy="Marwina Admin";
  selectedApp.docs[idx].verifiedOn=new Date().toISOString().split("T")[0];
  selectedApp.docs[idx].issues=[];
  activityLog.unshift({time:new Date().toLocaleString(),admin:"Marwina Admin",appId:selectedApp.id,doc:selectedApp.docs[idx].name,action:"Verified",notes:"Marked as verified."});
  showToast("Document marked as Verified");
  renderDocCards();
}
function unsetDoc(idx){
  selectedApp.docs[idx].status="Under Review";
  selectedApp.docs[idx].verifiedBy="";
  selectedApp.docs[idx].verifiedOn="";
  selectedApp.docs[idx].issues=[];
  showToast("Document status reset");
  renderDocCards();
}
function viewFullDoc(name){showToast(`Opening "${name}" full view...`);}

/* ═══ REJECT MODAL ═══ */
function rejectDoc(idx){
  rejectTargetIdx=idx;
  const doc=selectedApp.docs[idx];
  document.getElementById("rejectDocName").innerText=doc.name+" — "+doc.type;
  document.getElementById("rejectReason").value=doc.issues.length?doc.issues[0]:"";
  document.getElementById("rejectError").classList.add("hidden");
  document.querySelectorAll(".chip").forEach(c=>c.classList.remove("selected"));
  if(doc.issues.length) document.querySelectorAll(".chip").forEach(c=>{if(c.dataset.reason===doc.issues[0]) c.classList.add("selected");});
  document.getElementById("rejectModal").classList.add("open");
  lucide.createIcons();
}
function closeRejectModal(){document.getElementById("rejectModal").classList.remove("open");rejectTargetIdx=null;}
function selectChip(el){
  document.querySelectorAll(".chip").forEach(c=>c.classList.remove("selected"));
  el.classList.add("selected");
  document.getElementById("rejectReason").value=el.dataset.reason;
  document.getElementById("rejectError").classList.add("hidden");
}
function confirmReject(){
  const reason=document.getElementById("rejectReason").value.trim();
  if(!reason){document.getElementById("rejectError").classList.remove("hidden");return;}
  selectedApp.docs[rejectTargetIdx].status="Rejected";
  selectedApp.docs[rejectTargetIdx].issues=[reason];
  activityLog.unshift({time:new Date().toLocaleString(),admin:"Marwina Admin",appId:selectedApp.id,doc:selectedApp.docs[rejectTargetIdx].name,action:"Rejected",notes:reason.substring(0,50)});
  showToast("Document rejected: "+reason.substring(0,40)+(reason.length>40?"…":""),"warn");
  closeRejectModal();
  renderDocCards();
}

/* ═══ MODAL ACTIONS ═══ */
function markVerified(){
  selectedApp.remarks=document.getElementById("remarks").value;
  selectedApp.status="Verified";
  activityLog.unshift({time:new Date().toLocaleString(),admin:"Marwina Admin",appId:selectedApp.id,doc:"All Documents",action:"Verified",notes:selectedApp.remarks||"Marked as fully verified."});
  showToast(selectedApp.id+" marked as Verified ✓");
  closeModal(); renderTable(); renderDashboard();
}
function markIncomplete(){
  selectedApp.remarks=document.getElementById("remarks").value;
  selectedApp.status="Incomplete";
  activityLog.unshift({time:new Date().toLocaleString(),admin:"Marwina Admin",appId:selectedApp.id,doc:"Application",action:"Incomplete",notes:selectedApp.remarks||"Marked as incomplete."});
  showToast(selectedApp.id+" marked as Incomplete","warn");
  closeModal(); renderTable(); renderDashboard();
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
  applications.forEach(a=>rows.push([a.id,a.name,a.course,a.status,a.lastActivity]));
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
renderDashboard();
renderTable();
renderStudents();
renderHistory();