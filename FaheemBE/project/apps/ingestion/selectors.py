from typing import Optional
from django.db.models import QuerySet
from .models import ProcessingJob, IdentityMatchCandidate, JobState, CandidateStatus


def get_pending_processing_jobs() -> QuerySet[ProcessingJob]:
    """استرجاع مهام المعالجة المعلقة."""
    return ProcessingJob.objects.filter(state=JobState.PENDING).order_by('created_at')


def get_candidates_for_job(job_id: str, status: Optional[str] = None) -> QuerySet[IdentityMatchCandidate]:
    """استرجاع مرشحي المطابقة لمهمة معالجة معينة."""
    qs = IdentityMatchCandidate.objects.filter(job_id=job_id)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by('id')
