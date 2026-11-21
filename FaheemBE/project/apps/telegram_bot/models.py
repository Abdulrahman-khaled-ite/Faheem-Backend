from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    STUDENT = 'STUDENT', _('طالب')
    ADMIN = 'ADMIN', _('مشرف')
    GUEST = 'GUEST', _('زائر')


class ClaimStatus(models.TextChoices):
    PENDING = 'PENDING', _('قيد المراجعة والتحقق')
    APPROVED = 'APPROVED', _('تم التحقق وتثبيت الملكية')
    REJECTED = 'REJECTED', _('مرفوض')


class TelegramUser(models.Model):
    """
    مستخدم قناة تليغرام:
    يمثل حساب منصة تليغرام مفصولاً تماماً عن السجل الأكاديمي،
    ولا يُربط بالسجل إلا بعد إثبات الملكية وتوثيقها.
    """
    telegram_id = models.BigIntegerField(unique=True, db_index=True, verbose_name=_('معرف تليغرام الرقمي'))
    username = models.CharField(max_length=150, null=True, blank=True, verbose_name=_('اسم المستخدم @'))
    first_name = models.CharField(max_length=150, blank=True, verbose_name=_('الاسم الأول'))
    last_name = models.CharField(max_length=150, blank=True, verbose_name=_('الكنية / اسم العائلة'))
    linked_record = models.OneToOneField(
        'academic.AcademicRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='telegram_user',
        verbose_name=_('السجل الأكاديمي المربوط')
    )
    role = models.CharField(
        max_length=50,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        verbose_name=_('الدور')
    )
    is_verified = models.BooleanField(default=False, db_index=True, verbose_name=_('تم توثيق الهوية الأكاديمية'))
    active_wizard_state = models.JSONField(default=dict, blank=True, verbose_name=_('حالة المعالج التفاعلي للرفع'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ أول انضمام'))
    last_interaction_at = models.DateTimeField(auto_now=True, verbose_name=_('آخر تفاعل'))

    class Meta:
        db_table = 'telegram_users'
        verbose_name = _('مستخدم تليغرام')
        verbose_name_plural = _('مستخدمو تليغرام')

    def __str__(self):
        user_desc = f"@{self.username}" if self.username else str(self.telegram_id)
        verified_badge = "✓" if self.is_verified else "✗"
        return f"TG:{user_desc} [{verified_badge}]"


class StudentClaimRequest(models.Model):
    """
    طلب ربط حساب الطالب بسجله الأكاديمي:
    يمنع التخمين أو الاستيلاء على السجل بالاسم المجرد،
    ويتطلب التحقق من رقم الامتحان والسنة والدليل.
    """
    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='claim_requests',
        verbose_name=_('مستخدم تليغرام')
    )
    academic_record = models.ForeignKey(
        'academic.AcademicRecord',
        on_delete=models.CASCADE,
        related_name='claim_requests',
        verbose_name=_('السجل الأكاديمي المطلوب')
    )
    claimed_exam_number = models.CharField(max_length=10, verbose_name=_('الرقم الامتحاني المدعى'))
    claimed_academic_year = models.CharField(max_length=50, verbose_name=_('السنة الأكاديمية'))
    status = models.CharField(
        max_length=50,
        choices=ClaimStatus.choices,
        default=ClaimStatus.PENDING,
        db_index=True,
        verbose_name=_('حالة الطلب')
    )
    decision_reason = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('سبب القرار أو الرفض'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ تقديم الطلب'))
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ اتخاذ القرار'))

    class Meta:
        db_table = 'student_claim_requests'
        verbose_name = _('طلب ربط سجل أكاديمي')
        verbose_name_plural = _('طلبات ربط السجلات الأكاديمية')
        ordering = ['-created_at']


class InteractionLog(models.Model):
    """
    سجل تتبع تفاعلات البوت لضمان الـ Idempotency وتتبع الأخطاء.
    """
    telegram_user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='interaction_logs',
        verbose_name=_('المستخدم')
    )
    update_id = models.BigIntegerField(db_index=True, verbose_name=_('معرف تحديث تليغرام update_id'))
    command = models.CharField(max_length=100, blank=True, verbose_name=_('الأمر أو الـ Callback'))
    payload = models.JSONField(null=True, blank=True, verbose_name=_('بيانات الرسالة الواردة'))
    response_text = models.TextField(blank=True, verbose_name=_('نص الرد المرسل'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('وقت التفاعل'))

    class Meta:
        db_table = 'telegram_interaction_logs'
        verbose_name = _('سجل تفاعل تليغرام')
        verbose_name_plural = _('سجلات تفاعلات تليغرام')
        indexes = [
            models.Index(fields=['telegram_user', 'update_id']),
        ]
