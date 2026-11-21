from django.contrib import admin
from .models import OutboxEvent, ConsumerReceipt, NotificationAttempt


@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'aggregate_type', 'aggregate_id', 'delivery_state', 'created_at', 'delivered_at')
    list_filter = ('delivery_state', 'event_type')
    search_fields = ('aggregate_id', 'event_type')


@admin.register(ConsumerReceipt)
class ConsumerReceiptAdmin(admin.ModelAdmin):
    list_display = ('consumer_name', 'event', 'processed_at')
    list_filter = ('consumer_name',)


@admin.register(NotificationAttempt)
class NotificationAttemptAdmin(admin.ModelAdmin):
    list_display = ('recipient_id', 'status', 'attempt_kind', 'error_code', 'attempted_at')
    list_filter = ('status', 'attempt_kind')
