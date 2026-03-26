"""
Management command to fix Google SSO setup by removing duplicates and setting up properly.
Run with: python manage.py fix_google_sso
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp, SocialAccount
from allauth.socialaccount.providers.google.provider import GoogleProvider


class Command(BaseCommand):
    help = 'Fix Google SSO setup by removing duplicates'

    def handle(self, *args, **options):
        # Get or create the default site
        site, _ = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'WMSU Graduate School'
            }
        )
        
        # Update site domain if needed
        if site.domain == 'example.com':
            site.domain = 'localhost:8000'
            site.name = 'WMSU Graduate School'
            site.save()

        self.stdout.write(f"Site: {site.domain} (ID: {site.id})")
        
        # Check for existing SocialApps with Google provider
        existing_apps = SocialApp.objects.filter(provider=GoogleProvider.id)
        
        if existing_apps.count() > 1:
            self.stdout.write(self.style.WARNING(
                f'Found {existing_apps.count()} duplicate SocialApp entries for Google. Cleaning up...'
            ))
            
            # Keep the first one, delete the rest
            first_app = existing_apps.first()
            for app in existing_apps[1:]:
                self.stdout.write(f'  Deleting duplicate: {app.name} (ID: {app.id})')
                # First remove site associations
                app.sites.clear()
                # Then delete
                app.delete()
            
            app = first_app
            self.stdout.write(self.style.SUCCESS(f'Kept: {app.name} (ID: {app.id})'))
        elif existing_apps.count() == 1:
            app = existing_apps.first()
            self.stdout.write(f'Found existing SocialApp: {app.name} (ID: {app.id})')
        else:
            app = None
            self.stdout.write('No existing SocialApp found.')
        
        # Create or update the Google SocialApp
        if app is None:
            app = SocialApp.objects.create(
                provider=GoogleProvider.id,
                name='Google SSO',
                client_id='5275722877-ans6ljekru3amfoshkc7is9f3jb1dtrc.apps.googleusercontent.com',
                secret='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',
            )
            self.stdout.write(self.style.SUCCESS('Created new SocialApp'))
        
        # Update credentials
        app.client_id = '5275722877-ans6ljekru3amfoshkc7is9f3jb1dtrc.apps.googleusercontent.com'
        app.secret = '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'
        app.save()

        # Clear and re-associate the app with the site
        app.sites.clear()
        app.sites.add(site)
        app.save()

        self.stdout.write(self.style.SUCCESS('Google SSO setup complete!'))
        self.stdout.write('')
        self.stdout.write('Summary:')
        self.stdout.write(f'  - SocialApp ID: {app.id}')
        self.stdout.write(f'  - Provider: {app.provider}')
        self.stdout.write(f'  - Client ID: {app.client_id[:30]}...')
        self.stdout.write(f'  - Sites: {[s.domain for s in app.sites.all()]}')
        self.stdout.write('')
        self.stdout.write('Make sure to add this redirect URI in Google Cloud Console:')
        self.stdout.write('  http://localhost:8000/accounts/google/login/callback/')

