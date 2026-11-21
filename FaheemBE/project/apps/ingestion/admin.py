from django.contrib import admin
from .models import ProcessingJob, ProcessingAttempt, ProcessingArtifact, IdentityMatchCandidate


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_revision', 'state', 'requested_by', 'created_at', 'updated_at')
    list_filter = ('state',)
    search_fields = ('correlation_id', 'source_revision__drive_file__name')


@admin.register(IdentityMatchCandidate)
class IdentityMatchCandidateAdmin(admin.ModelAdmin):
    list_display = ('raw_name', 'exam_number', 'extracted_mark', 'candidate_record', 'score', 'status')
    list_filter = ('status',)
    search_fields = ('raw_name', 'normalized_name', 'exam_number')
