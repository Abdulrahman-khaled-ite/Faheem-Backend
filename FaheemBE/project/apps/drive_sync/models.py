from django.db import models
from django.utils.translation import gettext_lazy as _


class MaterialCategory(models.TextChoices):
    COURSES = 'دورات', _('دورات')
    ZANQA = 'زنقة', _('زنقة')
    LADDERS = 'سلالم', _('سلالم')
    SLIDES = 'سلايدات', _('سلايدات')
    LECTURES = 'محاضرات', _('محاضرات')
    APPENDIX = 'ملحق', _('ملحق')
    OTHER = 'أخرى', _('أخرى')


class StudyDepartment(models.TextChoices):
    GENERAL = 'عام', _('عام')
    SOFTWARE = 'برمجيات', _('برمجيات')
    AI = 'ذكاء', _('ذكاء')
    NETWORKS = 'شبكات', _('شبكات')


class DriveFile(models.Model):
    """
    يمثل الملف المسجل من Google Drive وموقعه في الشجرة.
    """
    drive_file_id = models.CharField(max_length=255, unique=True, db_index=True, verbose_name=_('معرف درايف'))
    name = models.CharField(max_length=500, verbose_name=_('اسم الملف'))
    mime_type = models.CharField(max_length=150, verbose_name=_('نوع الملف'))
    parent_folder_id = models.CharField(max_length=255, null=True, blank=True, db_index=True, verbose_name=_('معرف المجلد الأب'))
    drive_path = models.TextField(null=True, blank=True, verbose_name=_('المسار الكامل في درايف'))
    web_view_link = models.URLField(max_length=1000, null=True, blank=True, verbose_name=_('رابط المعاينة'))
    active = models.BooleanField(default=True, db_index=True, verbose_name=_('نشط / متاح'))
    last_seen_at = models.DateTimeField(auto_now=True, verbose_name=_('آخر ظهور'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإضافة'))

    class Meta:
        db_table = 'drive_files'
        verbose_name = _('ملف درايف')
        verbose_name_plural = _('ملفات درايف')

    def __str__(self):
        return f"{self.name} ({self.drive_file_id})"


class SourceRevision(models.Model):
    """
    إصدار الوثيقة: يُنشأ فقط عند حدوث تغير فعلي في بايتات الملف (مثل ملفات PDF للعلامات).
    """
    drive_file = models.ForeignKey(
        DriveFile,
        on_delete=models.PROTECT,
        related_name='revisions',
        verbose_name=_('ملف درايف')
    )
    pdf_digest = models.CharField(max_length=64, db_index=True, verbose_name=_('بصمة المحتوى SHA-256'))
    snapshot_ref = models.CharField(max_length=500, verbose_name=_('مسار النسخة المحفوظة محلياً'))
    file_size_bytes = models.BigIntegerField(default=0, verbose_name=_('حجم الملف بالبايت'))
    observed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الرصد'))

    class Meta:
        db_table = 'source_revisions'
        verbose_name = _('إصدار المصدر')
        verbose_name_plural = _('إصدارات المصادر')
        ordering = ['-observed_at']

    def __str__(self):
        return f"Rev:{self.id} for {self.drive_file.name} [{self.pdf_digest[:8]}]"


class SourceMetadataObservation(models.Model):
    """
    رصد التغير في البيانات الوصفية (مثل وقت التعديل على درايف) لتحديد أولوية الملف.
    """
    drive_file = models.ForeignKey(
        DriveFile,
        on_delete=models.CASCADE,
        related_name='metadata_observations',
        verbose_name=_('ملف درايف')
    )
    modified_time = models.DateTimeField(verbose_name=_('وقت التعديل في درايف'))
    created_time = models.DateTimeField(null=True, blank=True, verbose_name=_('وقت الإنشاء في درايف'))
    discovery_sequence = models.PositiveIntegerField(default=0, verbose_name=_('ترتيب الاكتشاف'))
    observed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الرصد'))

    class Meta:
        db_table = 'source_metadata_observations'
        verbose_name = _('رصد بيانات وصفية')
        verbose_name_plural = _('رصد البيانات الوصفية')


class EducationalMaterial(models.Model):
    """
    المكتبة والمواد الدراسية المصنفة حسب السنة، الاختصاص، المقرر، والتصنيف المعتمد.
    """
    drive_file = models.OneToOneField(
        DriveFile,
        on_delete=models.CASCADE,
        related_name='educational_material',
        verbose_name=_('ملف درايف')
    )
    study_year = models.PositiveSmallIntegerField(
        choices=[(1, _('السنة الأولى')), (2, _('السنة الثانية')), (3, _('السنة الثالثة')), (4, _('السنة الرابعة')), (5, _('السنة الخامسة'))],
        db_index=True,
        verbose_name=_('السنة الدراسية')
    )
    department = models.CharField(
        max_length=50,
        choices=StudyDepartment.choices,
        default=StudyDepartment.GENERAL,
        db_index=True,
        verbose_name=_('الاختصاص')
    )
    course_name = models.CharField(max_length=255, db_index=True, verbose_name=_('اسم المقرر'))
    category = models.CharField(
        max_length=50,
        choices=MaterialCategory.choices,
        db_index=True,
        verbose_name=_('التصنيف')
    )
    title = models.CharField(max_length=500, verbose_name=_('عنوان المادة أو المحاضرة'))
    is_published = models.BooleanField(default=True, db_index=True, verbose_name=_('منشور'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ الإضافة'))

    class Meta:
        db_table = 'educational_materials'
        verbose_name = _('مادة تعليمية')
        verbose_name_plural = _('المواد التعليمية')
        indexes = [
            models.Index(fields=['study_year', 'department', 'course_name', 'category']),
        ]

    def __str__(self):
        return f"[{self.course_name}] ({self.category}) {self.title}"
