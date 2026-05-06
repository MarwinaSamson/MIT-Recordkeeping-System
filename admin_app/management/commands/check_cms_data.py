"""
Management command to check CMS settings data.
Usage: python manage.py check_cms_data
"""
from django.core.management.base import BaseCommand
from admin_app.models import CMSSettings
import json


class Command(BaseCommand):
    help = 'Check and display CMS settings data'

    def handle(self, *args, **options):
        cms, created = CMSSettings.objects.get_or_create(pk=1)
        
        self.stdout.write('=== CMS Settings Data ===')
        self.stdout.write(f'Created: {created}')
        self.stdout.write(f'\nAdmission Requirements ({len(cms.admission_requirements)} items):')
        
        if cms.admission_requirements:
            self.stdout.write(json.dumps(cms.admission_requirements, indent=2))
        else:
            self.stdout.write('(empty)')
        
        self.stdout.write(f'\nCalendar Events ({len(cms.calendar_events)} items):')
        if cms.calendar_events:
            self.stdout.write(json.dumps(cms.calendar_events, indent=2))
        else:
            self.stdout.write('(empty)')
        
        self.stdout.write(self.style.SUCCESS('\nDone!'))
