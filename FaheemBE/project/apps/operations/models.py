import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class DeliveryState(models.TextChoices):
    PENDING = 'PENDING', _('قيد الانتظار')
    PROCESSING = 'PROCESSING', _('قيد الإرسال')
    DELIVERED = 'DELIVERED', _('تم التسليم')
    FAILED = 'FAILED', _('فشل الإرسال')


class OutboxEvent(models.Model):
    """
    نمط الصندوق الصادر (Transactional Outbox):
    يضمن تسجيل الأحداث داخل نفس المعاملة الذرية لقاعدة البيانات
    ثم تسليمها للمستهلكين (مثل بوت التليغرام) بدون فقدان.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, db_index=True, verbose_name=_('نوع الحدث'))
    aggregate_type = models.CharField(max_length=100, db_index=True, verbose_name=_('نوع الكيان'))
    aggregate_id = models.CharField(max_length=100, db_index=True, verbose_name=_('معرف الكيان'))
    payload = models.JSONField(verbose_name=_('بيانات الحدث'))
    delivery_state = models.CharField(
        max_length=20,
        choices=DeliveryState.choices,
        default=DeliveryState.PENDING,
        db_index=True,
        verbose_name=_('حالة التسليم')
    )
    retry_count = models.PositiveIntegerField(default=0, verbose_name=_('عدد المحاولات'))
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_('تاريخ الإنشاء'))
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاريخ التسليم'))

    class Meta:
        db_table = 'outbox_events'
        verbose_name = _('حدث صادر')
        verbose_name_plural = _('الأحداث الصادرة')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.event_type} - {self.aggregate_id} ({self.delivery_state})"


class ConsumerReceipt(models.Model):
    """
    إيصال استهلاك لمنع تكرار معالجة الحدث نفسه لكل مستهلك (Idempotency).
    """
    event = models.ForeignKey(
        OutboxEvent,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name=_('الحدث')
    )
    consumer_name = models.CharField(max_length=100, db_index=True, verbose_name=_('اسم المستهلك'))
    processed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ المعالجة'))

    class Meta:
        db_table = 'consumer_receipts'
        verbose_name = _('إيصال استهلاك')
        verbose_name_plural = _('إيصالات الاستهلاك')
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'consumer_name'],
                name='unique_consumer_event_receipt'
            )
        ]

    def __str__(self):
        return f"{self.consumer_name} -> {self.event_id}"


class NotificationAttempt(models.Model):
    """
    تتبع محاولات إرسال الإشعارات عبر تليغرام أو القنوات الأخرى للمشرفين والطلاب.
    """
    event = models.ForeignKey(
        OutboxEvent,
        on_delete=models.CASCADE,
        related_name='notification_attempts',
        verbose_name=_('الحدث')
    )
    recipient_id = models.CharField(max_length=100, db_index=True, verbose_name=_('معرف المستلم'))
    status = models.CharField(max_length=50, default='PENDING', verbose_name=_('الحالة'))
    attempt_kind = models.CharField(max_length=50, default='TELEGRAM_MESSAGE', verbose_name=_('نوع الإشعار'))
    error_code = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('رمز الخطأ'))
    error_detail = models.TextField(null=True, blank=True, verbose_name=_('تفاصيل الخطأ'))
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاريخ المحاولة'))

    class Meta:
        db_table = 'notification_attempts'
        verbose_name = _('محاولة إشعار')
        verbose_name_plural = _('محاولات الإشعار')
        ordering = ['-attempted_at']

    def __str__(self):
        return f"Notification to {self.recipient_id} [{self.status}]"
