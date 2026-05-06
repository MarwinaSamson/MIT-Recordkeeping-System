import re, json
from admin_app.models import CMSSettings, DocumentVerification
from students_app.models import Document
from django.contrib.auth.models import User

def title_to_key(title):
    if not title: return ""
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')

# Simulate exactly what the view sends to the template for user 41
user = User.objects.get(id=41)
cms = CMSSettings.objects.get(pk=1)

documents = Document.objects.filter(user=user)
verifications = DocumentVerification.objects.filter(document__user=user).select_related('document')

doc_by_key = {title_to_key(d.document_type): d for d in documents}
verif_by_key = {title_to_key(dv.document.document_type): dv for dv in verifications}

print("=== doc_by_key ===")
for k, v in doc_by_key.items():
    print(f"  {repr(k)} -> doc_id={v.id}")

print("\n=== verif_by_key ===")
for k, v in verif_by_key.items():
    print(f"  {repr(k)} -> status={v.status}")

print("\n=== document_status_map (what view sends) ===")
document_status_map = {}
for req in cms.admission_requirements:
    cms_key = title_to_key(req.get('title', ''))
    verif = verif_by_key.get(cms_key)
    doc   = doc_by_key.get(cms_key)
    if verif:
        vs = verif.status
        if vs == 'verified':       display = 'uploaded'
        elif vs == 'reviewing':    display = 'review'
        elif vs in ('rejected','incomplete'): display = 'missing'
        else:                      display = 'pending'
    elif doc:
        display = 'pending'
    else:
        display = 'missing'
    document_status_map[cms_key] = {'verification_status': display}
    print(f"  cms_key={repr(cms_key)} => display={repr(display)}")

print("\n=== JSON sent to frontend ===")
print(json.dumps(document_status_map, indent=2))

print("\n=== What frontend _titleToKey() produces from CMS titles ===")
for req in cms.admission_requirements:
    title = req.get('title','')
    print(f"  title={repr(title)} -> key={repr(title_to_key(title))}")