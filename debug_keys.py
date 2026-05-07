import re
from admin_app.models import CMSSettings, DocumentVerification
from students_app.models import Document

def title_to_key(title):
    if not title: return ""
    key = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    return key

print("="*60)
print("CMS ADMISSION REQUIREMENTS KEYS")
print("="*60)
cms = CMSSettings.objects.get(pk=1)
for req in cms.admission_requirements:
    t = req.get('title','')
    print(f"  title : {repr(t)}")
    print(f"  key   : {repr(title_to_key(t))}")

print("\n" + "="*60)
print("DB DOCUMENT KEYS (all users)")
print("="*60)
for doc in Document.objects.all().order_by('user_id','id'):
    print(f"  user_id={doc.user_id} | doc_id={doc.id}")
    print(f"  doc_type : {repr(doc.document_type)}")
    print(f"  key      : {repr(title_to_key(doc.document_type))}")

print("\n" + "="*60)
print("DOCUMENT VERIFICATION STATUS")
print("="*60)
for dv in DocumentVerification.objects.all().select_related('document'):
    print(f"  dv_id={dv.id} | doc_id={dv.document.id} | status={repr(dv.status)}")
    print(f"  doc_type : {repr(dv.document.document_type)}")
    print(f"  key      : {repr(title_to_key(dv.document.document_type))}")

print("\n" + "="*60)
print("KEY MATCH CHECK (CMS vs DB docs)")
print("="*60)
cms_keys = {title_to_key(r.get('title','')): r.get('title','') for r in cms.admission_requirements}
print("CMS keys dict:", cms_keys)
for doc in Document.objects.all().order_by('user_id','id'):
    doc_key = title_to_key(doc.document_type)
    match = cms_keys.get(doc_key, "*** NO MATCH ***")
    print(f"  user={doc.user_id} | doc_key={repr(doc_key)} => {repr(match)}")