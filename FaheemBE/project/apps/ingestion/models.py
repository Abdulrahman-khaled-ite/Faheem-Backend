import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class JobState(models.TextChoices):
    PENDING = 'PENDING', _('قيد الانتظار')
    PROCESSING = 'PROCESSING', _('قيد المعالجة')
    COMPLETED = 'COMPLETED', _('مكتمل بنجاح')
    FAILED = 'FAILED', _('فشل المعالجة')
    SUPERSEDED = 'SUPERSEDED', _('مستبدل بإصدار أحدث')


class CandidateStatus(models.TextChoices):
    CANDIDATE = 'CANDIDATE', _('مرشح للمطابقة')
    VERIFIED = 'VERIFIED', _('موثق ومطابق')
    AMBIGUOUS = 'AMBIGUOUS', _('ملتبس / بحاجة مراجعة')
    REJECTED = 'REJECTED', _('مرفوض')


class ProcessingJob(models.Model):
    """
    مهمة معالجة واستخراج لملف علامات أو وثيقة رسمية جديدة.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_revision = models.ForeignKey(
        'drive_sync.SourceRevision',
        on_delete=models.PROTECT,
        related_name='processing_jobs',
        verbose_name=_('إصدار المصدر')
    )
    state = models.CharField(
        max_length=50,
        choices=JobState.choices,
        default=JobState.PENDING,
        db_index=True,
        verbose_name=_('حالة المهمة')
    )
    reason = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('سبب الحالة أو التوقف'))
    requested_by = models.CharField(max_length=100, default='SYSTEM_POLL', verbose_name=_('الجهة الطالبة'))
    correlation_id = models.CharField(max_length=100, db_index=True, verbose_name=_('معرف التتبع Correlation ID'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        db_table = 'processing_jobs'
        verbose_name = _('مهمة معالجة')
        verbose_name_plural = _('مهام المعالجة')
        ordering = ['-created_at']

    def __str__(self):
        return f"Job:{self.id} [{self.state}] for Rev:{self.source_revision_id}"


class ProcessingAttempt(models.Model):
    """
    محاولات المعالجة القابلة لإعادة المحاولة المنفصلة (Retry).
    """
    job = models.ForeignKey(
        ProcessingJob,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('مهمة المعالجة')
    )
    attempt_number = models.PositiveIntegerField(default=1, verbose_name=_('رقم المحاولة'))
    state = models.CharField(max_length=50, default='STARTED', verbose_name=_('حالة المحاولة'))
    checkpoint_ref = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('نقطة الاستئناف'))
    error_summary = models.TextField(null=True, blank=True, verbose_name=_('ملخص الأخطاء'))
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('وقت البدء'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('وقت الانتهاء'))

    class Meta:
        db_table = 'processing_attempts'
        verbose_name = _('محاولة معالجة')
        verbose_name_plural = _('محاولات المعالجة')
        constraints = [
            models.UniqueConstraint(
                fields=['job', 'attempt_number'],
                name='unique_job_attempt_number'
            )
        ]


class ProcessingArtifact(models.Model):
    """
    الناتج الوسيط المعالج والمفهرس قبل الاعتماد والنشر.
    """
    job = models.ForeignKey(
        ProcessingJob,
        on_delete=models.CASCADE,
        related_name='artifacts',
        verbose_name=_('مهمة المعالجة')
    )
    manifest_ref = models.CharField(max_length=500, verbose_name=_('مسار بيان النتيجة Manifest Ref'))
    checksum = models.CharField(max_length=64, verbose_name=_('بصمة الـ Artifact SHA-256'))
    schema_version = models.CharField(max_length=20, default='1.0', verbose_name=_('إصدار المخطط'))
    row_counts = models.PositiveIntegerField(default=0, verbose_name=_('عدد الصفوف المستخرجة'))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ انتهاء الصلاحية'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        db_table = 'processing_artifacts'
        verbose_name = _('مخرج وسيط (Artifact)')
        verbose_name_plural = _('المخرجات الوسيطة')


class IdentityMatchCandidate(models.Model):
    """
    مرشح مطابقة الاسم ورقم الامتحان:
    يُخزن مفصولاً عن العلاقات الأكاديمية النهائية لحين التحقق.
    """
    job = models.ForeignKey(
        ProcessingJob,
        on_delete=models.CASCADE,
        related_name='match_candidates',
        verbose_name=_('مهمة المعالجة')
    )
    row_ref = models.CharField(max_length=255, verbose_name=_('مرجع الصف في الملف'))
    raw_name = models.CharField(max_length=255, verbose_name=_('الاسم الخام المستخرج'))
    normalized_name = models.CharField(max_length=255, db_index=True, verbose_name=_('الاسم المطبع'))
    exam_number = models.CharField(max_length=10, db_index=True, verbose_name=_('رقم الامتحان المستخرج'))
    extracted_mark = models.IntegerField(null=True, blank=True, verbose_name=_('العلامة المستخرجة'))
    candidate_record = models.ForeignKey(
        'academic.AcademicRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_candidates',
        verbose_name=_('السجل المرشح')
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, verbose_name=_('درجة الثقة 0-100'))
    evidence_ref = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('مرجع الدليل'))
    status = models.CharField(
        max_length=50,
        choices=CandidateStatus.choices,
        default=CandidateStatus.CANDIDATE,
        db_index=True,
        verbose_name=_('حالة المطابقة')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        db_table = 'identity_match_candidates'
        verbose_name = _('مرشح مطابقة هوية')
        verbose_name_plural = _('مرشحو مطابقة الهويات')
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['normalized_name', 'exam_number']),
        ]
