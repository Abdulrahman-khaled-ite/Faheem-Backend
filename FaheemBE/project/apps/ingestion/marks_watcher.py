import os
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from apps.drive_sync.models import DriveFile, SourceRevision
from apps.drive_sync.services import GoogleDriveService
from apps.ingestion.models import ProcessingJob, JobState
from apps.ingestion.services import IngestionPipelineService
from apps.operations.models import OutboxEvent, DeliveryState


class MarksWatcherService:
    """
    خدمة المراقبة التلقائية لمصادر علامات الكلية (الموقع الرسمي / مجلدات درايف):
    - الفحص الدوري لرصد أي ملف PDF جديد أو محدث للنتائج الامتحانية.
    - التحقق عبر بصمة الـ SHA-256 لضمان عدم تكرار المعالجة إذا لم تتغير البايتات.
    - إدخال الملف تلقائياً في خط الاستخراج Ingestion Pipeline وتوليد المرشحين والأدلة.
    """

    @classmethod
    def check_and_ingest_from_drive_folder(cls, marks_folder_id: Optional[str] = None) -> List[ProcessingJob]:
        """فحص مجلد (علامات جامعية) على Google Drive تلقائياً."""
        drive_service = GoogleDriveService()
        if not drive_service.is_configured():
            return []

        folder_id = marks_folder_id or settings.FAHEEM_CONFIG.get('GOOGLE_DRIVE_ROOT_FOLDER_ID')
        files = drive_service.list_folder_contents(folder_id)
        created_jobs = []

        staging_dir = Path(settings.BASE_DIR) / 'media' / 'staging' / 'marks'
        staging_dir.mkdir(parents=True, exist_ok=True)

        for file_info in files:
            # معالجة ملفات الـ PDF فقط
            if file_info.get('mimeType') != 'application/pdf' and not file_info.get('name', '').endswith('.pdf'):
                continue

            file_id = file_info['id']
            temp_path = staging_dir / f"{file_id}.pdf"

            try:
                # تنزيل الملف وحساب البصمة
                digest = drive_service.download_file_to_storage(file_id, temp_path)

                # التحقق إن كان هذا الإصدار مسجلاً مسبقاً بنفس البصمة
                if SourceRevision.objects.filter(pdf_digest=digest).exists():
                    if temp_path.exists():
                        temp_path.unlink()
                    continue

                # تسجيل ملف درايف وإصداره الجديد
                drive_file = drive_service.register_or_update_file(file_info)
                revision = drive_service.record_pdf_revision(drive_file, temp_path, digest)

                # إنشاء مهمة المعالجة وتشغيل الـ Ingestion Pipeline آلياً
                job = ProcessingJob.objects.create(
                    source_revision=revision,
                    state=JobState.PENDING,
                    correlation_id=f"auto_watch_{digest[:12]}",
                    requested_by="MARKS_AUTO_WATCHER"
                )

                # تنفيذ الاستخراج الفوري
                IngestionPipelineService.execute_job(job)
                created_jobs.append(job)

                # إشعار عبر الصندوق الصادر
                OutboxEvent.objects.create(
                    event_type='MARKS_PDF_INGESTED',
                    aggregate_type='ProcessingJob',
                    aggregate_id=str(job.id),
                    payload={
                        'file_name': file_info.get('name'),
                        'digest': digest,
                        'job_id': str(job.id),
                        'candidates_count': job.match_candidates.count(),
                        'discovered_at': timezone.now().isoformat()
                    },
                    delivery_state=DeliveryState.PENDING
                )

            except Exception as ex:
                pass

        return created_jobs

    @classmethod
    def check_and_ingest_from_url(cls, target_url: str, course_name: str) -> Optional[ProcessingJob]:
        """فحص وتنزيل ملف PDF من رابط مباشر أو صفحة ويب خارجية."""
        staging_dir = Path(settings.BASE_DIR) / 'media' / 'staging' / 'marks'
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            r = requests.get(target_url, stream=True, timeout=30)
            if r.status_code != 200:
                return None

            url_hash = hashlib.md5(target_url.encode('utf-8')).hexdigest()[:12]
            temp_path = staging_dir / f"web_{url_hash}.pdf"

            hasher = hashlib.sha256()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    hasher.update(chunk)

            digest = hasher.hexdigest()

            # تجنب التكرار
            if SourceRevision.objects.filter(pdf_digest=digest).exists():
                if temp_path.exists():
                    temp_path.unlink()
                return None

            drive_file, _ = DriveFile.objects.get_or_create(
                drive_file_id=f"web_marks_{url_hash}",
                defaults={
                    'name': f"علامات {course_name}.pdf",
                    'mime_type': 'application/pdf',
                    'web_view_link': target_url,
                    'active': True
                }
            )

            revision = SourceRevision.objects.create(
                drive_file=drive_file,
                pdf_digest=digest,
                snapshot_ref=str(temp_path),
                file_size_bytes=temp_path.stat().st_size
            )

            job = ProcessingJob.objects.create(
                source_revision=revision,
                state=JobState.PENDING,
                correlation_id=f"web_watch_{url_hash}",
                requested_by="WEB_SCRAPER"
            )

            IngestionPipelineService.execute_job(job)
            return job

        except Exception:
            return None
