# Admin Dashboard Backend Setup

## Overview

The admin dashboard backend includes:

- **Models**: Application, DocumentVerification, AdminActivityLog
- **Utilities**: Functions to fetch and process data from the database
- **API Views**: RESTful JSON endpoints for frontend
- **Management Command**: Initialize sample data for testing

## File Structure

```
admin_app/
├── models.py              # Database models for admin functionality
├── admin.py               # Django admin configuration
├── utils.py               # Utility functions for data fetching
├── urls.py                # URL routing including API endpoints
├── views/
│   ├── admin_dashboard_views.py  # Main dashboard view
│   └── api_views.py              # API endpoints for AJAX requests
├── migrations/
│   └── 0001_initial.py    # Initial migration
└── management/commands/
    └── initialize_admin_data.py  # Management command for sample data
```

## Models

### Application

Represents a student's application for a graduate program.

- Fields: user, program (MIT/MBA/MPA), application_id, status, submission_date, remarks
- Statuses: pending, reviewing, verified, incomplete, rejected

### DocumentVerification

Tracks verification status of individual documents.

- Fields: document (FK), status, verified_by, verified_at, remarks, rejection_reason
- Statuses: pending, reviewing, verified, incomplete, rejected

### AdminActivityLog

Logs all admin actions for audit trail.

- Fields: admin, application, document, action, notes, timestamp
- Actions: verified, rejected, incomplete, resubmit, note, comment

## Setup Instructions

### 1. Run Migrations

```bash
python manage.py makemigrations admin_app
python manage.py migrate admin_app
```

Or use the pre-created migration:

```bash
python manage.py migrate
```

### 2. Create Admin User (if not exists)

```bash
python manage.py createsuperuser
```

Or use the initialization command which creates a test admin automatically.

### 3. Initialize Sample Data (Optional)

```bash
python manage.py initialize_admin_data
```

This creates:

- 4 sample students with different statuses
- Sample documents for each student
- Document verifications
- Test admin user (username: admin, password: admin123)

To clear and recreate:

```bash
python manage.py initialize_admin_data --delete
```

## API Endpoints

All endpoints require superuser authentication.

### GET /admin-panel/api/applications/

Get all applications with summary statistics.

**Response:**

```json
{
  "success": true,
  "applications": [
    {
      "id": "MIT-0001",
      "name": "John Doe",
      "course": "MIT",
      "email": "john@example.com",
      "mobile": "+639123456789",
      "status": "verified",
      "submissionDate": "2026-02-21",
      "lastActivity": "2026-02-21",
      "remarks": "Sample remarks",
      "docCount": 5,
      "docStatuses": { "verified": 3, "pending": 2 }
    }
  ],
  "summary": {
    "total": 10,
    "pending": 2,
    "reviewing": 3,
    "verified": 3,
    "incomplete": 1,
    "rejected": 1
  }
}
```

### GET /admin-panel/api/application/{application_id}/

Get detailed information about a specific application.

**Response:**

```json
{
  "success": true,
  "application": {
    "id": "MIT-0001",
    "name": "John Doe",
    "email": "john@example.com",
    "mobile": "+639123456789",
    "course": "MIT",
    "status": "verified",
    "submissionDate": "2026-02-21",
    "lastActivity": "2026-02-21",
    "remarks": "Sample remarks",
    "documents": [
      {
        "id": 1,
        "name": "Transcript of Records",
        "type": "Academic Form",
        "status": "verified",
        "uploadDate": "2026-02-21",
        "verifiedBy": "admin",
        "verifiedOn": "2026-02-21",
        "issues": [],
        "file_name": "tor.pdf"
      }
    ]
  }
}
```

### POST /admin-panel/api/document/{document_id}/verify/

Mark a document as verified.

**Request Body:**

```json
{
  "remarks": "Document is clear and complete"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Document verified successfully",
  "verification": {
    "status": "verified",
    "verified_by": "admin",
    "verified_at": "2026-04-18 10:30"
  }
}
```

### POST /admin-panel/api/document/{document_id}/reject/

Mark a document as rejected.

**Request Body:**

```json
{
  "reason": "Document is blurry and unclear",
  "remarks": "Please resubmit with higher resolution"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Document rejected",
  "verification": {
    "status": "rejected",
    "reason": "Document is blurry and unclear"
  }
}
```

### GET /admin-panel/api/activity-log/?limit=20

Get recent admin activity logs.

**Response:**

```json
{
  "success": true,
  "logs": [
    {
      "time": "2026-04-18 10:30",
      "admin": "admin",
      "appId": "MIT-0001",
      "doc": "Transcript of Records",
      "action": "Verified Document",
      "notes": "Document is clear"
    }
  ]
}
```

### GET /admin-panel/api/dashboard-summary/

Get dashboard summary data.

**Response:**

```json
{
  "success": true,
  "summary": {
    "total": 10,
    "pending": 2,
    "reviewing": 3,
    "verified": 3,
    "incomplete": 1,
    "rejected": 1
  },
  "recent_apps": [
    {
      "id": "MIT-0001",
      "name": "John Doe",
      "course": "MIT",
      "status": "verified",
      "submission_date": "2026-02-21"
    }
  ],
  "verification_progress": {
    "verified": 15,
    "reviewing": 5,
    "pending": 8,
    "rejected": 2,
    "total": 30
  }
}
```

## Frontend Integration

The template receives context data:

```python
context = {
    'admin_name': str,          # Admin's full name
    'admin_email': str,         # Admin's email
    'summary': dict,            # Application counts by status
    'recent_applications': list,  # Last 5 applications
    'verification_progress': dict,  # Document verification stats
    'recent_activities': list,  # Last 10 admin activities
}
```

The JavaScript can fetch data from API endpoints for real-time updates.

## Usage Example

### In Template

```django
<p>Total Applications: {{ summary.total }}</p>
<p>Pending Review: {{ summary.pending }}</p>
<p>Verified: {{ summary.verified }}</p>
```

### In JavaScript (AJAX)

```javascript
fetch("/admin-panel/api/applications/")
  .then((response) => response.json())
  .then((data) => {
    if (data.success) {
      console.log(data.applications);
      console.log(data.summary);
    }
  });
```

## Security

- All endpoints require `login_required` decorator
- All endpoints require `@user_passes_test(is_superuser)` decorator
- Only superusers can access the admin dashboard
- CSRF protection enabled for POST requests

## Next Steps

1. Run migrations: `python manage.py migrate`
2. Initialize data: `python manage.py initialize_admin_data`
3. Create superuser: `python manage.py createsuperuser`
4. Run server: `python manage.py runserver`
5. Access dashboard: `http://localhost:8000/admin-panel/dashboard/`

## Troubleshooting

### ModuleNotFoundError: allauth

```bash
pip install -r requirements.txt
```

### Migration errors

```bash
python manage.py migrate admin_app
```

### No data showing

Run initialization command:

```bash
python manage.py initialize_admin_data
```
