# Google SSO Implementation TODO

## Phase 1: Google Cloud Console Setup (User Action Required)

- [x] Create Google Cloud Console project
- [x] Enable Google+ API / Google People API
- [x] Create OAuth 2.0 credentials
- [x] Get Client ID and Client Secret
- [x] Configure authorized redirect URIs

## Phase 2: Django Configuration

- [x] Install django-allauth package
- [x] Configure settings.py for allauth
- [x] Add authentication backends

## Phase 3: URL Configuration

- [x] Include allauth URLs in project urls.py

## Phase 4: Template Updates

- [x] Add "Sign in with Google" button to login.html
- [x] Add "Sign in with Google" button to register.html

## Phase 5: Customization

- [x] Create custom adapter to auto-create UserProfile for Google users
- [x] Auto-verify Google users (since Google already verified their email)

## Phase 6: Testing

- [ ] Test Google login flow
- [ ] Verify email verification still works for regular signup

## Phase 7: Database

- [x] Run migrations to create allauth tables

## Post-Setup Required

1. **Create SocialApp in Django Admin:**
   - Go to Django Admin → Social Accounts → Social applications
   - Add new social application with:
     - Provider: Google
     - Name: Google SSO
     - Client ID: 5275722877-ans6ljekru3amfoshkc7is9f3jb1dtrc.apps.googleusercontent.com
     - Key: (empty)
     - Secret: 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
   - Add site: example.com (or your domain)

2. **Configure Google Cloud Console:**
   - Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
   - For production, replace localhost with your domain
