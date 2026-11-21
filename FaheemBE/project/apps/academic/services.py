import hashlib
import json
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from .models import (
    PublicationScope,
    PublicationVersion,
    CurrentGrade,
    GradeComponent,
    GradeProvenance,
    AcademicRecord,
    PublicationState
)
from apps.operations.models import OutboxEvent, DeliveryState


class AcademicPublicationService:
    """
    سلطة النشر الأكاديمي الذرية (Atomic Publication Service):
    الجهة الوحيدة المخولة باعتماد وتعديل العلامات في جدول current_grades
    مع قفل النطاق على مستوى الصف (Row-Level Locking) وتسجيل أصل العلامة
    وإنشاء حدث Outbox للنشر التلقائي عبر Telegram.
    """

    @classmethod
    @transaction.atomic
    def commit_scope_results(
        cls,
        scope_id: int,
        source_revision_id: int,
        results_rows: List[Dict[str, Any]],
        correlation_id: str,
        reason: str = "اعتماد نتائج امتحانية رسمية"
    ) -> PublicationScope:
        """
        تنفيذ عملية النشر الذرية لنطاق محدد.
        results_rows عبارة عن قائمة قواميس تحتوي:
        [
            {
                'academic_record_id': 123,
                'final_mark': 85,           # 0-100 أو None
                'absence_reason': None,     # سبب الغياب إن وجد
                'source_row_ref': 'page:2/row:15',
                'components': [{'name': 'نظري', 'mark': 55}, {'name': 'عملي', 'mark': 30}]
            },
            ...
        ]
        """
        # 1. قفل صف نطاق النشر لمنع التضارب المتزامن (Row-level lock)
        scope = PublicationScope.objects.select_for_update().get(id=scope_id)

        # 2. توليد البصمة المعيارية (Canonical Fingerprint) للنتائج
        canonical_str = json.dumps(
            sorted([
                {
                    'rec': r['academic_record_id'],
                    'mark': r.get('final_mark'),
                    'abs': r.get('absence_reason')
                }
                for r in results_rows
            ], key=lambda x: x['rec']),
            sort_keys=True
        )
        new_fingerprint = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

        # التحقق من عدم التكرار (No-Change)
        if scope.state == PublicationState.PUBLISHED and scope.fingerprint == new_fingerprint:
            # لم يحدث أي تغيير في العلامات
            return scope

        # 3. زيادة رقم الإصدار وإنشاء PublicationVersion
        new_version_num = scope.version + 1 if scope.state == PublicationState.PUBLISHED else 1
        pub_version = PublicationVersion.objects.create(
            scope=scope,
            version=new_version_num,
            fingerprint=new_fingerprint
        )

        # 4. تحديث/إنشاء العلامات الحالية وأدلة الأصل (Provenance)
        for row in results_rows:
            record_id = row['academic_record_id']
            final_mark = row.get('final_mark')
            absence_reason = row.get('absence_reason')
            row_ref = row.get('source_row_ref', 'auto_extracted')

            # إنشاء أصل العلامة
            provenance = GradeProvenance.objects.create(
                source_revision_id=source_revision_id,
                source_row_ref=row_ref,
                decision_reason=reason,
                evidence_digest=new_fingerprint
            )

            # تحديث أو إنشاء العلامة الحالية للطالب داخل هذا النطاق
            grade_obj, created = CurrentGrade.objects.update_or_create(
                scope=scope,
                academic_record_id=record_id,
                defaults={
                    'final_mark': final_mark,
                    'absence_reason': absence_reason,
                    'provenance': provenance,
                    'publication_version': pub_version,
                }
            )

            # تحديث الأجزاء المكونة للعلامة إن وجدت
            components = row.get('components', [])
            if components:
                grade_obj.components.all().delete()
                component_objs = [
                    GradeComponent(
                        current_grade=grade_obj,
                        component_name=c.get('name', 'عام'),
                        mark_value=c.get('mark', 0),
                        evidence_ref=row_ref
                    )
                    for c in components
                ]
                GradeComponent.objects.bulk_create(component_objs)

        # 5. تحديث نطاق النشر
        scope.version = new_version_num
        scope.fingerprint = new_fingerprint
        scope.state = PublicationState.PUBLISHED
        scope.save()

        # 6. تسجيل الحدث في الصندوق الصادر (Transactional Outbox)
        OutboxEvent.objects.create(
            event_type='MARKS_PUBLISHED',
            aggregate_type='PublicationScope',
            aggregate_id=str(scope.id),
            payload={
                'scope_id': scope.id,
                'course_name': scope.course.name,
                'academic_year': scope.academic_year.label,
                'exam_session': scope.exam_session.label,
                'version': scope.version,
                'correlation_id': correlation_id,
                'total_students_count': len(results_rows),
                'published_at': timezone.now().isoformat()
            },
            delivery_state=DeliveryState.PENDING
        )

        return scope
