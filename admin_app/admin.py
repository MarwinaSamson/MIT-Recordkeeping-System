from django.contrib import admin
from .models import Application, DocumentVerification, AdminActivityLog


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

