from django.contrib import admin
from .models import DriveFile, SourceRevision, SourceMetadataObservation, EducationalMaterial


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'drive_file_id', 'mime_type', 'active', 'last_seen_at')
    search_fields = ('name', 'drive_file_id', 'drive_path')
    list_filter = ('active', 'mime_type')


@admin.register(SourceRevision)
class SourceRevisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'drive_file', 'pdf_digest', 'file_size_bytes', 'observed_at')
    search_fields = ('drive_file__name', 'pdf_digest')


@admin.register(EducationalMaterial)
class EducationalMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_name', 'study_year', 'department', 'category', 'is_published')
    list_filter = ('study_year', 'department', 'category', 'is_published')
    search_fields = ('title', 'course_name')
