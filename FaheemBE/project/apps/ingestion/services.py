import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List
from django.db import transaction
from django.utils import timezone
from .models import ProcessingJob, ProcessingAttempt, ProcessingArtifact, IdentityMatchCandidate, JobState, CandidateStatus
from .extractors.pdf_marks_extractor import PDFMarksExtractor
from apps.academic.models import AcademicRecord, YearlyExamIdentity


class IngestionPipelineService:
    """
    خدمة خط استخراج ومعالجة العلامات:
    - تحليل ملفات الـ PDF واستخراج الصفوف بدقة.
    - مطابقة الأسماء والأرقام الامتحانية مع قاعدة بيانات الطلاب.
    - توليد الـ ProcessingArtifact ومقترحات المطابقة لحين اعتمادها في النواة الأكاديمية.
    """

    @classmethod
    @transaction.atomic
    def execute_job(cls, job: ProcessingJob) -> ProcessingJob:
        attempt_number = job.attempts.count() + 1
        attempt = ProcessingAttempt.objects.create(
            job=job,
            attempt_number=attempt_number,
            state='STARTED'
        )

        job.state = JobState.PROCESSING
        job.save(update_fields=['state', 'updated_at'])

        try:
            pdf_path = job.source_revision.snapshot_ref
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"Source PDF file not found at {pdf_path}")

            # استخراج الصفوف
            extracted_rows = PDFMarksExtractor.extract_rows_from_pdf(pdf_path)

            candidates_to_create = []
            for row in extracted_rows:
                # محاولة مطابقة السجل الأكاديمي أولاً بالرقم الامتحاني في الهوية السنوية
                matched_record = None
                status = CandidateStatus.CANDIDATE
                score = 50.0

                # فحص بالرقم الامتحاني
                yearly_identity = YearlyExamIdentity.objects.filter(
                    exam_number=row['exam_number']
                ).select_related('academic_record').first()

                if yearly_identity:
                    matched_record = yearly_identity.academic_record
                    score = 90.0
                    status = CandidateStatus.VERIFIED
                else:
                    # فحص بالاسم المطبع
                    name_match = AcademicRecord.objects.filter(
                        normalized_name=row['normalized_name']
                    ).first()
                    if name_match:
                        matched_record = name_match
                        score = 75.0

                candidate = IdentityMatchCandidate(
                    job=job,
                    row_ref=row['row_ref'],
                    raw_name=row['raw_name'],
                    normalized_name=row['normalized_name'],
                    exam_number=row['exam_number'],
                    extracted_mark=row['final_mark'],
                    candidate_record=matched_record,
                    score=score,
                    status=status
                )
                candidates_to_create.append(candidate)

            IdentityMatchCandidate.objects.bulk_create(candidates_to_create)

            # إنشاء الـ ProcessingArtifact
            manifest_content = json.dumps([r['row_ref'] for r in extracted_rows])
            manifest_digest = hashlib.sha256(manifest_content.encode('utf-8')).hexdigest()
            ProcessingArtifact.objects.create(
                job=job,
                manifest_ref=f"manifests/job_{job.id}.json",
                checksum=manifest_digest,
                row_counts=len(extracted_rows)
            )

            job.state = JobState.COMPLETED
            job.save(update_fields=['state', 'updated_at'])

            attempt.state = 'COMPLETED'
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=['state', 'completed_at'])

        except Exception as ex:
            job.state = JobState.FAILED
            job.reason = str(ex)[:250]
            job.save(update_fields=['state', 'reason', 'updated_at'])

            attempt.state = 'FAILED'
            attempt.error_summary = str(ex)
            attempt.completed_at = timezone.now()
            attempt.save(update_fields=['state', 'error_summary', 'completed_at'])

        return job
