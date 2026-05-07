#!/usr/bin/env python
"""
Test script to verify document key mapping for user 41
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recordkeeping_proj.settings")
django.setup()

from students_app.models import Document
from admin_app.models import DocumentVerification
from students_app.views.student_views import _title_to_key
from students_app.views.api_views import get_document_key

# Get user 41
from django.contrib.auth.models import User
try:
    user = User.objects.get(id=41)
    print(f"\n=== Testing Document Mapping for User: {user.username} (id={user.id}) ===\n")
    
    # Get documents
    documents = Document.objects.filter(user=user)
    print(f"Documents found: {documents.count()}")
    
    for doc in documents:
        print(f"\nDocument ID: {doc.id}")
        print(f"  Type: {doc.document_type}")
        print(f"  File: {doc.file_name or doc.file.name}")
        
        # Test key mapping
        key_from_title = _title_to_key(doc.document_type)
        key_from_api = get_document_key(doc.document_type)
        
        print(f"  Key (from _title_to_key): {key_from_title}")
        print(f"  Key (from get_document_key): {key_from_api}")
        
        # Check verification status
        verification = DocumentVerification.objects.filter(document=doc).first()
        if verification:
            print(f"  Verification Status: {verification.status}")
        else:
            print(f"  Verification Status: None (not yet verified)")
    
    # Show what API would return
    print(f"\n=== Simulating API Response ===\n")
    doc_statuses = {}
    for doc in documents:
        key = get_document_key(doc.document_type)
        if key:
            verification = DocumentVerification.objects.filter(document=doc).first()
            if verification:
                status_map = {
                    'verified': 'approved',
                    'reviewing': 'review',
                    'rejected': 'rejected',
                    'pending': 'pending',
                    'incomplete': 'pending',
                }
                frontend_status = status_map.get(verification.status, 'pending')
                doc_statuses[key] = {
                    'status': frontend_status,
                    'uploaded': True,
                    'rejection_reason': verification.rejection_reason or '',
                }
            else:
                doc_statuses[key] = {
                    'status': 'pending',
                    'uploaded': True,
                    'rejection_reason': '',
                }
    
    import json
    print(json.dumps(doc_statuses, indent=2))
    
except User.DoesNotExist:
    print("User 41 not found!")
