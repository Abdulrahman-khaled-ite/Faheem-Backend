from typing import Optional
from django.db.models import QuerySet
from .models import OutboxEvent, DeliveryState


def get_pending_outbox_events(limit: int = 50) -> QuerySet[OutboxEvent]:
    """استرجاع الأحداث غير المسلمة بعد لجدول الإرسال."""
    return OutboxEvent.objects.filter(
        delivery_state=DeliveryState.PENDING
    ).order_by('created_at')[:limit]


def get_failed_outbox_events() -> QuerySet[OutboxEvent]:
    """استرجاع الأحداث التي تعثر تسليمها لمراجعتها."""
    return OutboxEvent.objects.filter(
        delivery_state=DeliveryState.FAILED
    ).order_by('-created_at')
