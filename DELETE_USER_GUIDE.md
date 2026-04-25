# Delete User Account - PowerShell Guide

This guide helps you delete a Google account user and restart the enrollment process.

## Option 1: Delete User via Django Management Command (Recommended)

### Step 1: Open PowerShell

```powershell
# Navigate to your project directory
cd "C:\Users\lenovo\Documents\GitHub\MIT-Recordkeeping-System"
```

### Step 2: Activate Virtual Environment

```powershell
# Activate the virtual environment
.\admissionVenv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: List All Users

```powershell
# Enter Django shell to see all users
python manage.py shell

# In the Python shell, type:
from django.contrib.auth.models import User
for user in User.objects.all():
    print(f"ID: {user.id}, Email: {user.email}, Username: {user.username}")

# Exit with: exit()
```

### Step 4: Delete User by Email

```powershell
# Run this command (replace "user@example.com" with the actual email)
python manage.py shell

# In the Python shell, type:
from django.contrib.auth.models import User
user = User.objects.get(email="user@example.com")
print(f"Deleting user: {user.email}")
user.delete()
print("User deleted successfully!")

# Exit with: exit()
```

---

## Option 2: Delete Using Interactive Django Shell (Easier)

```powershell
# Start Django shell
python manage.py shell
```

Then paste this code:

```python
from django.contrib.auth.models import User
from students_app.models import UserProfile

# List all users first
print("=" * 50)
print("USERS IN SYSTEM:")
print("=" * 50)
for user in User.objects.all():
    print(f"ID: {user.id} | Email: {user.email} | Username: {user.username}")

print("\n" + "=" * 50)
email_to_delete = input("Enter email of user to delete: ").strip()
print("=" * 50 + "\n")

try:
    user = User.objects.get(email=email_to_delete)
    print(f"Found user: {user.email}")
    print(f"This will delete:")
    print(f"  - User account")
    print(f"  - Personal details")
    print(f"  - Educational background")
    print(f"  - Working student info")
    print(f"  - All uploaded documents")
    print(f"  - Privacy consent")
    print(f"  - Application record")

    confirm = input("\nConfirm deletion? (yes/no): ").strip().lower()
    if confirm == "yes":
        user.delete()
        print("\n✓ User deleted successfully!")
        print("They can now sign up again with the same email.")
    else:
        print("Deletion cancelled.")
except User.DoesNotExist:
    print(f"✗ User with email '{email_to_delete}' not found.")
```

---

## Option 3: Delete Specific User by Email (One-liner)

```powershell
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
user = User.objects.get(email="user@example.com")
user.delete()
print("User deleted!")
EOF
```

Replace `"user@example.com"` with the actual email address.

---

## Option 4: Delete All Test Users (CAUTION!)

⚠️ **WARNING: This deletes ALL users. Only use in development!**

```powershell
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
User.objects.all().delete()
print("All users deleted!")
EOF
```

---

## What Gets Deleted

When you delete a user, **ALL** related records are automatically deleted due to Django's cascade deletion:

✓ User account
✓ UserProfile (email verification status)
✓ PersonalDetails (name, address, etc.)
✓ EducationalBackground (school history)
✓ WorkingStudent (employment info)
✓ Documents (uploaded files)
✓ DocumentVerification (admin verification records)
✓ PrivacyConsent (consent records)
✓ Application (application record)
✓ SocialAccount (Google OAuth link)
✓ Notifications

---

## After Deletion - How to Restart

### Step 1: User Signs Up Again

- User goes to `/signup/` page
- Uses the SAME email address
- Creates a new password

### Step 2: Fresh Start

- New UserProfile created
- No documents or enrollment history
- Starts from Personal Details page

### Step 3: Re-authenticate with Google

- If using Google SSO, the old OAuth connection is gone
- User can sign in with new Google account or use email/password

---

## Troubleshooting

### Error: "User matching query does not exist"

```powershell
# The email doesn't exist. Check the correct email first:
python manage.py shell
from django.contrib.auth.models import User
User.objects.all().values_list('email', flat=True)
```

### Error: "Execution Policy"

```powershell
# Allow PowerShell scripts to run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Database is locked

```powershell
# Close all Django shells/servers and try again
# Or restart PowerShell
```

---

## Quick Reference

| Task               | Command                                            |
| ------------------ | -------------------------------------------------- |
| List all users     | `python manage.py shell` then `User.objects.all()` |
| Find user by email | `User.objects.get(email="email@domain.com")`       |
| Delete user        | `user.delete()`                                    |
| Clear all users    | `User.objects.all().delete()`                      |
| Exit Django shell  | `exit()`                                           |

---

## Database Backup (Recommended Before Deletion)

Before deleting users, backup your database:

```powershell
# Backup PostgreSQL database
pg_dump -U postgres -h localhost mit_recordkeeping_db > backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql

# Restore from backup if needed
psql -U postgres -h localhost mit_recordkeeping_db < backup_20240425_120000.sql
```

---

## Video Steps (Simplified)

1. Open PowerShell
2. Navigate to project: `cd C:\Users\lenovo\Documents\GitHub\MIT-Recordkeeping-System`
3. Activate venv: `.\admissionVenv\Scripts\Activate.ps1`
4. Start shell: `python manage.py shell`
5. Delete user:
   ```python
   from django.contrib.auth.models import User
   user = User.objects.get(email="theirEmail@example.com")
   user.delete()
   ```
6. Exit: `exit()`
7. User can now sign up again!
