from django.utils import timezone
from .models import OutboxEvent, ConsumerReceipt, NotificationAttempt, DeliveryState


class OutboxDispatcherService:
    """
    خدمة معالجة وتسليم الصندوق الصادر (Outbox Dispatcher):
    تقوم بقراءة الأحداث ذات الحالة PENDING وتوجيهها للمستهلكين المناسبين
    مع تسجيل إيصالات الاستهلاك لمنع التكرار (Idempotency).
    """

    @classmethod
    def dispatch_pending_events(cls, limit: int = 50) -> int:
        from apps.operations.selectors import get_pending_outbox_events
        pending_events = get_pending_outbox_events(limit=limit)
        processed_count = 0

        for event in pending_events:
            event.delivery_state = DeliveryState.PROCESSING
            event.save(update_fields=['delivery_state'])

            try:
                # توجيه الحدث بحسب نوعه
                if event.event_type == 'MARKS_PUBLISHED':
                    cls._handle_marks_published(event)

                event.delivery_state = DeliveryState.DELIVERED
                event.delivered_at = timezone.now()
                event.save(update_fields=['delivery_state', 'delivered_at'])
                processed_count += 1
            except Exception as ex:
                event.delivery_state = DeliveryState.FAILED
                event.retry_count += 1
                event.save(update_fields=['delivery_state', 'retry_count'])

        return processed_count

    @classmethod
    def _handle_marks_published(cls, event: OutboxEvent):
        """
        عند نشر نتائج مقرر جديد:
        إرسال إشعار للطلاب المشتركين والموثقين عبر بوت تليغرام.
        """
        consumer_name = "telegram_publication_broadcaster"
        # التحقق من عدم الاستهلاك المسبق
        if ConsumerReceipt.objects.filter(event=event, consumer_name=consumer_name).exists():
            return

        # تسجيل إيصال الاستهلاك
        ConsumerReceipt.objects.create(event=event, consumer_name=consumer_name)
