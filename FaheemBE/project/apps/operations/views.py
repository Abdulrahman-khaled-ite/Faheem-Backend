from rest_framework import viewsets
from .models import OutboxEvent, NotificationAttempt
from .serializers import OutboxEventSerializer, NotificationAttemptSerializer


class OutboxEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OutboxEvent.objects.all().order_by('-created_at')
    serializer_class = OutboxEventSerializer
    filterset_fields = ['event_type', 'delivery_state']


class NotificationAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NotificationAttempt.objects.all().order_by('-attempted_at')
    serializer_class = NotificationAttemptSerializer
