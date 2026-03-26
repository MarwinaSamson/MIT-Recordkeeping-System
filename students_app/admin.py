from django.contrib import admin
from .models import PersonalDetails, EducationalBackground, Document, UserProfile

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_email_verified', 'created_at']
    list_filter = ['is_email_verified', 'created_at']
    search_fields = ['user__email', 'user__username']

@admin.register(PersonalDetails)
class PersonalDetailsAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'created_at']
    list_filter = ['gender', 'civil_status', 'created_at']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(EducationalBackground)
class EducationalBackgroundAdmin(admin.ModelAdmin):
    list_display = ['user', 'level', 'school_name', 'degree_course', 'year_completed']
    list_filter = ['level', 'year_completed']
    search_fields = ['user__username', 'school_name', 'degree_course']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'file_name', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['user__username', 'file_name']
