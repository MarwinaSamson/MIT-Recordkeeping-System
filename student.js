const DOC_ITEMS=[
  {key:"deansRec",label:"Dean's Recommendation",required:true},
  {key:"tor",label:"Transcript of Records (TOR)",required:true},
  {key:"honorableDismissal",label:"Honorable Dismissal",required:true},
  {key:"psa",label:"PSA Birth Certificate",required:true},
  {key:"gsat",label:"GSAT Result",required:true},
];
const DOC_STATUS={
  deansRec:{status:"approved",note:"Verified and accepted."},
  tor:{status:"review",note:"Currently under review by the registrar's office."},
  honorableDismissal:{status:"rejected",note:"Document appears illegible. Please re-upload a clearer copy."},
  psa:{status:"pending",note:"Awaiting submission."},
  gsat:{status:"pending",note:"Awaiting submission."},
};
let notifications=[
  {id:1,icon:"fa-times-circle",color:"#DC2626",bg:"#FEF2F2",title:"Document Rejected",msg:"Your Honorable Dismissal was rejected. Please re-upload a clearer, legible copy for re-review.",time:"2 hours ago",read:false},
  {id:2,icon:"fa-search",color:"#1D4ED8",bg:"#EFF6FF",title:"Document Under Review",msg:"Your Transcript of Records (TOR) is currently being reviewed by the Registrar's Office.",time:"Yesterday",read:false},
  {id:3,icon:"fa-check-circle",color:"#15803D",bg:"#F0FDF4",title:"Document Approved",msg:"Your Dean's Recommendation letter has been verified and approved. No further action is required.",time:"2 days ago",read:true},
  {id:4,icon:"fa-bell",color:"#B45309",bg:"#FFFBEB",title:"Deadline Reminder",msg:"The document submission deadline is March 15, 2026. Ensure all required documents are uploaded on time.",time:"3 days ago",read:true},
];
let toastTimer=null,isEditing=false,currentUploadKey=null;

/* THEME */
function toggleTheme(){
  const isDark=document.documentElement.classList.toggle('dark');
  localStorage.setItem('mitTheme',isDark?'dark':'light');
  document.getElementById('themeIcon').className=isDark?'fas fa-sun':'fas fa-moon';
}
function initTheme(){
  const saved=localStorage.getItem('mitTheme');
  const prefersDark=window.matchMedia('(prefers-color-scheme:dark)').matches;
  if(saved==='dark'||(saved===null&&prefersDark)){
    document.documentElement.classList.add('dark');
    document.getElementById('themeIcon').className='fas fa-sun';
  }
}

window.addEventListener('DOMContentLoaded',()=>{
  initTheme();
  loadPersonalData();buildMiniDocList();buildDocGrid();buildStatusSummary();
  buildNotifications();buildNotifPreview();updateProgress();loadProfileFields();setFieldsDisabled(true);
});

function greetUser(){
  const p=JSON.parse(localStorage.getItem("mitPersonal")||"{}");
  const name=p.firstName||"Noellene Pearl A. Villarcampo";
  const h=new Date().getHours();
  const g=h<12?"Good morning":h<17?"Good afternoon":"Good evening";
  document.getElementById("welcomeName").textContent=`${g}, ${name}.`;
}

function loadPersonalData(){
  const p=JSON.parse(localStorage.getItem("mitPersonal")||"{}");
  const full=[p.firstName,p.lastName].filter(Boolean).join(" ")||"Noellene Pearl A. Villarcampo";
  const ini=[p.firstName,p.lastName].filter(Boolean).map(n=>n[0]).join("").toUpperCase()||"JD";
  document.getElementById("sidebarName").textContent=full;
  ["sidebarAvatar","topAvatar","profileAvatarBig"].forEach(id=>document.getElementById(id).textContent=ini);
  document.getElementById("profileName").textContent=full;
  document.getElementById("profileEmail").textContent=p.email||"—";
  greetUser();
}

function updateProgress(){
  const docs=JSON.parse(localStorage.getItem("mitDocs")||"{}");
  const done=DOC_ITEMS.filter(d=>!!docs[d.key]).length;
  const pct=Math.round(done/DOC_ITEMS.length*100);
  document.getElementById("progressPercent").textContent=pct+"%";
  document.getElementById("progBar").style.width=pct+"%";
  document.getElementById("progLabel").textContent=`${done} of ${DOC_ITEMS.length} submitted`;
  document.getElementById("progressRing").style.strokeDashoffset=283-(283*pct/100);
  document.getElementById("statDocs").textContent=`${done}/${DOC_ITEMS.length}`;
  document.getElementById("statApproved").textContent=Object.values(DOC_STATUS).filter(d=>d.status==="approved").length;
  document.getElementById("statReview").textContent=Object.values(DOC_STATUS).filter(d=>d.status==="review").length;
}

function buildMiniDocList(){
  const docs=JSON.parse(localStorage.getItem("mitDocs")||"{}");
  document.getElementById("miniDocList").innerHTML=DOC_ITEMS.map(d=>{
    const u=!!docs[d.key],s=DOC_STATUS[d.key];
    const sc=u?pillClass(s.status):"pill-draft",sl=u?capFirst(s.status):"Not uploaded";
    const ic=u?(s.status==="approved"?"var(--green)":s.status==="rejected"?"var(--red)":"var(--blue)"):"#D1D5DB";
    return `<div class="mini-row"><i class="fas ${u?"fa-check-circle":"fa-circle"}" style="color:${ic}"></i><span>${d.label}</span><span class="pill ${sc}">${sl}</span></div>`;
  }).join("");
}

function buildDocGrid(){
  const docs=JSON.parse(localStorage.getItem("mitDocs")||"{}");
  document.getElementById("docGrid").innerHTML=DOC_ITEMS.map(d=>{
    const u=!!docs[d.key],s=DOC_STATUS[d.key],fn=docs[d.key]||null;
    const sc=u?pillClass(s.status):"pill-draft",sl=u?capFirst(s.status):"Not uploaded";
    const rc=u?s.status:"";
    const ibg=u?(s.status==="approved"?"var(--green-bg)":s.status==="rejected"?"var(--red-light)":"var(--blue-bg)"):"var(--rule-light)";
    const ic=u?(s.status==="approved"?"var(--green)":s.status==="rejected"?"var(--red)":"var(--blue)"):"#D1D5DB";
    const nc=s.status==="rejected"?"color:var(--red)":s.status==="approved"?"color:var(--green)":"color:var(--ink-4)";
    const ni=s.status==="rejected"?"fa-exclamation-circle":s.status==="approved"?"fa-check-circle":"fa-info-circle";
    const nh=u&&s.note?`<div class="doc-note" style="${nc}"><i class="fas ${ni}" style="margin-right:4px;font-size:.65rem"></i>${s.note}</div>`:"";
    return `<div class="doc-row ${rc}">
      <div class="doc-icon-wrap" style="background:${ibg}"><i class="fas ${u?"fa-file-alt":"fa-file"}" style="color:${ic}"></i></div>
      <div style="flex:1;min-width:0">
        <div class="doc-name">${d.label}${d.required?'<span style="color:var(--red);margin-left:2px">*</span>':""}</div>
        <div class="doc-meta">${fn||"No file uploaded"}</div>${nh}
      </div>
      <div class="doc-actions">
        <span class="pill ${sc}">${sl}</span>
        <button class="btn btn-outline btn-xs" onclick="triggerUploadFor('${d.key}')">
          <i class="fas ${u?"fa-sync-alt":"fa-upload"}" style="font-size:.65rem"></i>${u?"Replace":"Upload"}
        </button>
      </div>
    </div>`;
  }).join("");
}

function buildStatusSummary(){
  const docs=JSON.parse(localStorage.getItem("mitDocs")||"{}");
  const c={approved:0,review:0,rejected:0,pending:0};
  DOC_ITEMS.forEach(d=>{c[!!docs[d.key]?DOC_STATUS[d.key].status:"pending"]++;});
  document.getElementById("statusSummary").innerHTML=[
    {key:"approved",label:"Approved",icon:"fa-check-circle",color:"var(--green)"},
    {key:"review",label:"Under Review",icon:"fa-search",color:"var(--blue)"},
    {key:"rejected",label:"Rejected",icon:"fa-times-circle",color:"var(--red)"},
    {key:"pending",label:"Not Uploaded",icon:"fa-circle",color:"#D1D5DB"},
  ].map(i=>`<div style="display:flex;align-items:center;gap:9px;padding:5px 0;border-bottom:1px solid var(--rule-light)">
    <i class="fas ${i.icon}" style="color:${i.color};width:14px;font-size:.75rem;flex-shrink:0"></i>
    <span style="font-size:.79rem;color:var(--ink-3);flex:1">${i.label}</span>
    <span style="font-size:.82rem;font-weight:700;color:var(--ink)">${c[i.key]}</span>
  </div>`).join("");
}

function buildNotifications(){
  const u=notifications.filter(n=>!n.read).length;
  document.getElementById("notifBadge").textContent=u||"";
  document.getElementById("notifBadge").style.display=u?"":"none";
  document.getElementById("topNotifDot").style.display=u?"block":"none";
  document.getElementById("notifList").innerHTML=notifications.length
    ?notifications.map(n=>renderN(n)).join("")
    :`<div style="text-align:center;padding:32px 0;color:var(--ink-4);font-size:.82rem">No notifications</div>`;
}

function buildNotifPreview(){
  document.getElementById("notifPreview").innerHTML=notifications.slice(0,3).map(n=>renderN(n,true)).join("");
}

function renderN(n,compact=false){
  return `<div class="notif-item ${n.read?"":"unread"}" onclick="readNotif(${n.id})">
    <div class="notif-icon-wrap" style="background:${n.bg}"><i class="fas ${n.icon}" style="color:${n.color}"></i></div>
    <div style="flex:1;min-width:0">
      <div class="notif-title">${n.title}${!n.read?'<span class="notif-dot"></span>':""}</div>
      <div class="notif-msg" ${compact?'style="display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden"':""}>${n.msg}</div>
      <div class="notif-time">${n.time}</div>
    </div>
  </div>`;
}

function readNotif(id){notifications=notifications.map(n=>n.id===id?{...n,read:true}:n);buildNotifications();buildNotifPreview();}
function markAllRead(){notifications=notifications.map(n=>({...n,read:true}));buildNotifications();buildNotifPreview();showToast("All notifications marked as read");}

function triggerUploadFor(key){currentUploadKey=key;document.getElementById("fileInput").click();}
function handleFileSelect(e){const f=e.target.files[0];if(f)processUpload(f);e.target.value="";}
function handleDrop(e){e.preventDefault();document.getElementById("dropzone").classList.remove("dragover");const f=e.dataTransfer.files[0];if(f)processUpload(f);}

function processUpload(file){
  if(file.size>10*1024*1024){showToast("File exceeds 10 MB limit","error");return;}
  const docs=JSON.parse(localStorage.getItem("mitDocs")||"{}");
  if(currentUploadKey){docs[currentUploadKey]=file.name;currentUploadKey=null;}
  else{
    const m=DOC_ITEMS.find(d=>!docs[d.key]);
    if(!m){showToast("All documents uploaded. Use Replace to swap.","info");return;}
    docs[m.key]=file.name;
  }
  localStorage.setItem("mitDocs",JSON.stringify(docs));
  buildDocGrid();buildMiniDocList();buildStatusSummary();updateProgress();
  const no=document.getElementById("uploadNotice");
  document.getElementById("uploadNoticeTxt").textContent=`"${file.name}" uploaded successfully`;
  no.classList.remove("hidden");
  setTimeout(()=>no.classList.add("hidden"),4500);
  showToast(`"${file.name}" uploaded`);
}

function loadProfileFields(){
  const p=JSON.parse(localStorage.getItem("mitPersonal")||"{}");
  if(p.firstName)document.getElementById("pFirstName").value=p.firstName;
  if(p.lastName)document.getElementById("pLastName").value=p.lastName;
  if(p.dob)document.getElementById("pDob").value=p.dob;
  if(p.gender)document.getElementById("pGender").value=p.gender;
  if(p.contact)document.getElementById("pContact").value=p.contact;
  if(p.email)document.getElementById("pEmail").value=p.email;
  if(p.address)document.getElementById("pAddress").value=p.address;
  if(p.college)document.getElementById("profileCollege").textContent=p.college;
  if(p.grad)document.getElementById("profileGrad").textContent=p.grad;
}

function setFieldsDisabled(d){
  ["pFirstName","pLastName","pDob","pGender","pContact","pEmail","pAddress"].forEach(id=>{document.getElementById(id).disabled=d;});
}

function toggleEditMode(){
  isEditing=!isEditing;
  setFieldsDisabled(!isEditing);
  document.getElementById("editBtnLabel").textContent=isEditing?"Cancel":"Edit Profile";
  document.getElementById("savePersonalBtns").style.display=isEditing?"flex":"none";
  document.getElementById("editIndicator").style.display=isEditing?"block":"none";
}

function cancelEdit(){
  isEditing=false;setFieldsDisabled(true);
  document.getElementById("editBtnLabel").textContent="Edit Profile";
  document.getElementById("savePersonalBtns").style.display="none";
  document.getElementById("editIndicator").style.display="none";
  loadProfileFields();
}

function saveProfile(){
  const p={
    firstName:document.getElementById("pFirstName").value.trim(),
    lastName:document.getElementById("pLastName").value.trim(),
    dob:document.getElementById("pDob").value,
    gender:document.getElementById("pGender").value,
    contact:document.getElementById("pContact").value.trim(),
    email:document.getElementById("pEmail").value.trim(),
    address:document.getElementById("pAddress").value.trim(),
  };
  localStorage.setItem("mitPersonal",JSON.stringify(p));
  loadPersonalData();loadProfileFields();
  isEditing=false;setFieldsDisabled(true);
  document.getElementById("editBtnLabel").textContent="Edit Profile";
  document.getElementById("savePersonalBtns").style.display="none";
  document.getElementById("editIndicator").style.display="none";
  showToast("Profile updated successfully");
}

const PAGE_META={overview:{breadcrumb:"Dashboard",title:"Overview"},documents:{breadcrumb:"Dashboard",title:"My Documents"},notifications:{breadcrumb:"Dashboard",title:"Notifications"},profile:{breadcrumb:"Account",title:"My Profile"}};

function switchPage(pageId,el){
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.getElementById("page-"+pageId).classList.add("active");
  document.querySelectorAll(".nav-item").forEach(n=>n.classList.remove("active"));
  if(el)el.classList.add("active");
  const m=PAGE_META[pageId]||{breadcrumb:"",title:""};
  document.getElementById("topBreadcrumb").textContent=m.breadcrumb;
  document.getElementById("topTitle").textContent=m.title;
  if(pageId==="overview"){buildMiniDocList();buildNotifPreview();updateProgress();}
  if(pageId==="documents"){buildDocGrid();buildStatusSummary();}
  if(pageId==="notifications")buildNotifications();
  if(pageId==="profile")loadProfileFields();
  closeSidebar();window.scrollTo(0,0);
}

function toggleSidebar(){document.getElementById("sidebar").classList.toggle("open");document.getElementById("overlay").classList.toggle("active");}
function closeSidebar(){document.getElementById("sidebar").classList.remove("open");document.getElementById("overlay").classList.remove("active");}
function handleLogout(){if(confirm("Sign out of MIT Student Portal?"))showToast("Signed out successfully");}

function showToast(msg,type="success"){
  const c={success:"#4ADE80",error:"#F87171",info:"#60A5FA"};
  const i={success:"fa-check-circle",error:"fa-exclamation-circle",info:"fa-info-circle"};
  document.getElementById("toastText").textContent=msg;
  document.getElementById("toastIcon").style.color=c[type];
  document.getElementById("toastIcon").className=`fas ${i[type]}`;
  const t=document.getElementById("toast");t.classList.remove("hidden");
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.add("hidden"),3500);
}

function pillClass(s){return{approved:"pill-approved",review:"pill-review",rejected:"pill-rejected",pending:"pill-pending",draft:"pill-draft"}[s]||"pill-draft";}
function capFirst(s){return s?s[0].toUpperCase()+s.slice(1):"";}