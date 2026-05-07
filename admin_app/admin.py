from django.contrib import admin
from .models import Application, DocumentVerification, AdminActivityLog
from .models import SchoolYear
from .models import Prospectus, ProspectusYear, ProspectusSemester, ProspectusSubject, ProspectusAssignment, Program


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id', 'user', 'program', 'status', 'submission_date')
    list_filter = ('program', 'status', 'submission_date')
    search_fields = ('application_id', 'user__email', 'user__username')
    readonly_fields = ('application_id', 'submission_date', 'created_at', 'updated_at')
    fieldsets = (
        ('Application Info', {
            'fields': ('application_id', 'user', 'program', 'status')
        }),
        ('Details', {
            'fields': ('remarks',)
        }),
        ('Timestamps', {
            'fields': ('submission_date', 'last_activity', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ('document', 'status', 'verified_by', 'verified_at')
    list_filter = ('status', 'verified_at', 'created_at')
    search_fields = ('document__file_name', 'remarks')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Document', {
            'fields': ('document',)
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at')
        }),
        ('Feedback', {
            'fields': ('rejection_reason', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'admin', 'application', 'action', 'document')
    list_filter = ('action', 'timestamp', 'admin')
    search_fields = ('application__application_id', 'notes', 'admin__username')
    readonly_fields = ('timestamp',)
    fieldsets = (
        ('Activity Info', {
            'fields': ('admin', 'application', 'document', 'action')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'is_active', 'is_archived', 'start_date', 'end_date']
    list_filter = ['status', 'is_active', 'is_archived']


@admin.register(Prospectus)
class ProspectusAdmin(admin.ModelAdmin):
    list_display = ('name', 'program_name', 'program_code', 'is_active', 'created_at')
    search_fields = ('name', 'program_name', 'program_code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProspectusYear)
class ProspectusYearAdmin(admin.ModelAdmin):
    list_display = ('prospectus', 'label', 'order')
    list_filter = ('prospectus',)


@admin.register(ProspectusSemester)
class ProspectusSemesterAdmin(admin.ModelAdmin):
    list_display = ('year', 'label', 'order')
    list_filter = ('year',)


@admin.register(ProspectusSubject)
class ProspectusSubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'semester', 'lec', 'lab', 'total')
    search_fields = ('code', 'title')


@admin.register(ProspectusAssignment)
class ProspectusAssignmentAdmin(admin.ModelAdmin):
    list_display = ('prospectus', 'program_name', 'program_code', 'intake_year', 'created_at')
    search_fields = ('program_name', 'program_code')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

