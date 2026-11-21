from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class PublicationState(models.TextChoices):
    PENDING = 'PENDING', _('بانتظار التحقق والنشر')
    PUBLISHED = 'PUBLISHED', _('منشور رسمي')
    STALE = 'STALE', _('قديم / بحاجة تحديث')
    ARCHIVED = 'ARCHIVED', _('مؤرشف')


class AcademicRecord(models.Model):
    """
    السجل الأكاديمي الدائم للطالب:
    يمثل هوية الطالب الثابتة والمستقلة عن أي سنة دراسية أو رقم امتحاني أو حساب تليغرام.
    """
    id = models.BigAutoField(primary_key=True, verbose_name=_('المعرف الداخلي'))
    official_name = models.CharField(max_length=255, db_index=True, verbose_name=_('الاسم الرسمي بالجامعة'))
    normalized_name = models.CharField(max_length=255, db_index=True, blank=True, verbose_name=_('الاسم المطبع للبحث'))
    university_id = models.CharField(max_length=50, null=True, blank=True, unique=True, verbose_name=_('الرقم الجامعي'))
    national_id_hash = models.CharField(max_length=64, null=True, blank=True, verbose_name=_('تشفير الرقم الوطني'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))

    class Meta:
        db_table = 'academic_records'
        verbose_name = _('سجل أكاديمي')
        verbose_name_plural = _('السجلات الأكاديمية')

    def __str__(self):
        return f"[{self.id}] {self.official_name}"


class AcademicYear(models.Model):
    """
    السنة الأكاديمية (مثل 2024-2025).
    """
    label = models.CharField(max_length=50, unique=True, verbose_name=_('تسمية السنة'))
    start_year = models.PositiveIntegerField(verbose_name=_('سنة البدء'))

    class Meta:
        db_table = 'academic_years'
        verbose_name = _('سنة أكاديمية')
        verbose_name_plural = _('السنوات الأكاديمية')
        ordering = ['-start_year']

    def __str__(self):
        return self.label


class YearlyExamIdentity(models.Model):
    """
    الهوية الامتحانية السنوية:
    الرقم الامتحاني (5 خانات) فريد في سنة معينة لجميع المقررات،
    ويرتبط بالسجل الأكاديمي المثبت بعد التحقق.
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='exam_identities',
        verbose_name=_('السنة الأكاديمية')
    )
    exam_number = models.CharField(max_length=10, db_index=True, verbose_name=_('الرقم الامتحاني'))
    academic_record = models.ForeignKey(
        AcademicRecord,
        on_delete=models.CASCADE,
        related_name='yearly_identities',
        verbose_name=_('السجل الأكاديمي')
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ التحقق والتثبيت'))
    evidence_ref = models.CharField(max_length=255, blank=True, verbose_name=_('مرجع الدليل'))

    class Meta:
        db_table = 'yearly_exam_identities'
        verbose_name = _('هوية امتحانية سنوية')
        verbose_name_plural = _('الهويات الامتحانية السنوية')
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'exam_number'],
                name='unique_year_exam_number'
            ),
            models.UniqueConstraint(
                fields=['academic_year', 'academic_record'],
                name='unique_year_academic_record'
            ),
        ]

    def __str__(self):
        return f"{self.academic_year}: #{self.exam_number} -> {self.academic_record.official_name}"


class Course(models.Model):
    """
    المقرر الدراسي وهوية المنهاج الأصلية.
    """
    name = models.CharField(max_length=255, db_index=True, verbose_name=_('اسم المقرر'))
    code = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('رمز المقرر'))
    original_study_year = models.PositiveSmallIntegerField(
        choices=[(1, _('السنة الأولى')), (2, _('السنة الثانية')), (3, _('السنة الثالثة')), (4, _('السنة الرابعة')), (5, _('السنة الخامسة'))],
        verbose_name=_('سنة الدراسة الأصلية للمقرر')
    )
    department = models.CharField(
        max_length=50,
        default='عام',
        verbose_name=_('الاختصاص')
    )
    semester = models.PositiveSmallIntegerField(
        choices=[(1, _('الفصل الأول')), (2, _('الفصل الثاني'))],
        default=1,
        verbose_name=_('الفصل الدراسي')
    )

    class Meta:
        db_table = 'courses'
        verbose_name = _('مقرر دراسي')
        verbose_name_plural = _('المقررات الدراسية')

    def __str__(self):
        return f"{self.name} ({self.get_original_study_year_display()} - {self.department})"


class ExamSession(models.Model):
    """
    الدورة الامتحانية (دورة أولى، دورة ثانية، تكميلي).
    """
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('السنة الأكاديمية')
    )
    label = models.CharField(max_length=100, verbose_name=_('تسمية الدورة'))
    official_order = models.PositiveSmallIntegerField(default=1, verbose_name=_('الترتيب الرسمي'))

    class Meta:
        db_table = 'exam_sessions'
        verbose_name = _('دورة امتحانية')
        verbose_name_plural = _('الدورات الامتحانية')
        constraints = [
            models.UniqueConstraint(
                fields=['academic_year', 'official_order'],
                name='unique_year_session_order'
            )
        ]

    def __str__(self):
        return f"{self.academic_year.label} - {self.label}"


class PublicationScope(models.Model):
    """
    نطاق النشر الذري (Atomic Publication Scope):
    صف القفل لحماية المعاملة؛ يتم النشر وتحديث العلامات بشكل ذري لكل (مقرر، سنة، دورة).
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name='publication_scopes',
        verbose_name=_('المقرر')
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='publication_scopes',
        verbose_name=_('السنة الأكاديمية')
    )
    exam_session = models.ForeignKey(
        ExamSession,
        on_delete=models.PROTECT,
        related_name='publication_scopes',
        verbose_name=_('الدورة الامتحانية')
    )
    version = models.PositiveIntegerField(default=1, verbose_name=_('رقم الإصدار'))
    fingerprint = models.CharField(max_length=64, blank=True, verbose_name=_('بصمة النشر Canonical Digest'))
    state = models.CharField(
        max_length=50,
        choices=PublicationState.choices,
        default=PublicationState.PENDING,
        db_index=True,
        verbose_name=_('حالة النشر')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإنشاء'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ آخر تحديث'))

    class Meta:
        db_table = 'publication_scopes'
        verbose_name = _('نطاق نشر')
        verbose_name_plural = _('نطاقات النشر')
        constraints = [
            models.UniqueConstraint(
                fields=['course', 'academic_year', 'exam_session'],
                name='unique_scope_course_year_session'
            )
        ]

    def __str__(self):
        return f"{self.course.name} | {self.academic_year.label} | {self.exam_session.label} (v{self.version})"


class GradeProvenance(models.Model):
    """
    أصل ومصدر العلامة:
    يوثق بدقة المستند والسطر وسبب اختيار العلامة حتى في حالات الـ Fallback.
    """
    source_revision = models.ForeignKey(
        'drive_sync.SourceRevision',
        on_delete=models.PROTECT,
        related_name='grade_provenances',
        verbose_name=_('إصدار المصدر')
    )
    source_row_ref = models.CharField(max_length=255, verbose_name=_('مرجع الصف في الملف'))
    decision_reason = models.CharField(max_length=255, verbose_name=_('سبب القرار'))
    evidence_digest = models.CharField(max_length=64, blank=True, verbose_name=_('بصمة الدليل'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ التسجيل'))

    class Meta:
        db_table = 'grade_provenance'
        verbose_name = _('أصل العلامة')
        verbose_name_plural = _('أصول العلامات')

    def __str__(self):
        return f"Provenance #{self.id} -> Row: {self.source_row_ref}"


class PublicationVersion(models.Model):
    """
    تاريخ وسجل إصدارات النشر المعتمدة.
    """
    scope = models.ForeignKey(
        PublicationScope,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name=_('نطاق النشر')
    )
    version = models.PositiveIntegerField(verbose_name=_('رقم الإصدار'))
    fingerprint = models.CharField(max_length=64, verbose_name=_('بصمة الإصدار'))
    committed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الاعتماد'))

    class Meta:
        db_table = 'publication_versions'
        verbose_name = _('إصدار نشر')
        verbose_name_plural = _('إصدارات النشر')
        constraints = [
            models.UniqueConstraint(
                fields=['scope', 'version'],
                name='unique_scope_version'
            )
        ]


class CurrentGrade(models.Model):
    """
    العلامة الرسمية الحالية المعتمدة:
    فريدة لكل (طالب، نطاق نشر). الصفر علامة صحيحة، والغياب يُسجل كـ NULL مع سبب.
    """
    scope = models.ForeignKey(
        PublicationScope,
        on_delete=models.PROTECT,
        related_name='grades',
        verbose_name=_('نطاق النشر')
    )
    academic_record = models.ForeignKey(
        AcademicRecord,
        on_delete=models.PROTECT,
        related_name='grades',
        verbose_name=_('السجل الأكاديمي')
    )
    final_mark = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('العلامة النهائية')
    )
    absence_reason = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('سبب الغياب إن وجد'))
    provenance = models.ForeignKey(
        GradeProvenance,
        on_delete=models.PROTECT,
        related_name='grades',
        verbose_name=_('أصل ومصدر العلامة')
    )
    publication_version = models.ForeignKey(
        PublicationVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grades',
        verbose_name=_('إصدار النشر')
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ التحديث'))

    class Meta:
        db_table = 'current_grades'
        verbose_name = _('علامة حالية')
        verbose_name_plural = _('العلامات الحالية')
        constraints = [
            models.UniqueConstraint(
                fields=['scope', 'academic_record'],
                name='unique_scope_academic_record_grade'
            )
        ]

    def __str__(self):
        mark_display = self.final_mark if self.final_mark is not None else f"غائب ({self.absence_reason})"
        return f"{self.academic_record.official_name} -> {self.scope.course.name}: {mark_display}"


class GradeComponent(models.Model):
    """
    تفاصيل وأجزاء العلامة (نظري، عملي، أعمال سنة) دون التأثير على القيمة الرسمية.
    """
    current_grade = models.ForeignKey(
        CurrentGrade,
        on_delete=models.CASCADE,
        related_name='components',
        verbose_name=_('العلامة الحالية')
    )
    component_name = models.CharField(max_length=100, verbose_name=_('اسم الجزء'))
    mark_value = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('قيمة العلامة'))
    evidence_ref = models.CharField(max_length=255, blank=True, verbose_name=_('مرجع الدليل'))

    class Meta:
        db_table = 'grade_components'
        verbose_name = _('جزء علامة')
        verbose_name_plural = _('أجزاء العلامات')


class DerivedAcademicState(models.Model):
    """
    الحسابات الأكاديمية المشتقة (المعدل التراكمي، الفصلي، حالة التخرج، ترفع/رسوب).
    توضح حالة الحداثة (Fresh / Stale) لتمييز تأخر الحساب عن العلامات الرسمية.
    """
    academic_record = models.ForeignKey(
        AcademicRecord,
        on_delete=models.CASCADE,
        related_name='derived_states',
        verbose_name=_('السجل الأكاديمي')
    )
    calculation_kind = models.CharField(max_length=50, verbose_name=_('نوع الحساب'))
    input_fingerprint = models.CharField(max_length=64, verbose_name=_('بصمة المدخلات'))
    freshness_status = models.CharField(max_length=50, default='FRESH', verbose_name=_('حالة الحداثة'))
    value_json = models.JSONField(verbose_name=_('البيانات المحسوبة'))
    calculated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاريخ الحساب'))

    class Meta:
        db_table = 'derived_academic_states'
        verbose_name = _('حالة أكاديمية مشتقة')
        verbose_name_plural = _('الحالات الأكاديمية المشتقة')
