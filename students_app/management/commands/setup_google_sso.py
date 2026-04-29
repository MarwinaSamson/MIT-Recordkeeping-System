"""
Management command to set up Google SSO programmatically.
Run with: python manage.py setup_google_sso
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.google.provider import GoogleProvider


class Command(BaseCommand):
    help = 'Set up Google SSO programmatically'

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

        # Create or update the Google SocialApp
        app, created = SocialApp.objects.get_or_create(
            provider=GoogleProvider.id,
            name='Google SSO',
            defaults={
                'client_id': '5275722877-ans6ljekru3amfoshkc7is9f3jb1dtrc.apps.googleusercontent.com',
                'secret': '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',
            }
        )

        if not created:
            app.client_id = '5275722877-ans6ljekru3amfoshkc7is9f3jb1dtrc.apps.googleusercontent.com'
            app.secret = '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'
            app.save()

        # Associate the app with the site
        if site not in app.sites.all():
            app.sites.add(site)
            app.save()

        if created:
            self.stdout.write(self.style.SUCCESS(
                'Created Google SocialApp and associated with site'))
        else:
            self.stdout.write(self.style.SUCCESS('Updated Google SocialApp'))

        self.stdout.write(self.style.SUCCESS('Google SSO setup complete!'))
        self.stdout.write('')
        self.stdout.write(
            'Make sure to add this redirect URI in Google Cloud Console:')
        self.stdout.write(
            '  http://localhost:8000/accounts/google/login/callback/')
