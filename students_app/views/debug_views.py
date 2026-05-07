"""
API view to check document and CMS data
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from admin_app.models import CMSSettings, DocumentVerification
from students_app.models import Document


@login_required
def api_check_doc_data(request):
    """Check document and verification data for current user"""
    user = request.user
    
    # Get documents
    documents = Document.objects.filter(user=user)
    doc_list = []
    for doc in documents:
        verification = DocumentVerification.objects.filter(document=doc).first()
        doc_list.append({
            'id': doc.id,
            'document_type': doc.document_type,
            'file_name': doc.file_name,
            'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            'verification_status': verification.status if verification else 'no_verification',
            'verification_id': verification.id if verification else None,
        })
    
    # Get CMS settings
    cms = CMSSettings.objects.get_or_create(pk=1)[0]
    
    return JsonResponse({
        'user': user.username,
        'documents': doc_list,
        'cms_admission_requirements': cms.admission_requirements,
    }, indent=2)
