from rest_framework import serializers
from .models import OutboxEvent, ConsumerReceipt, NotificationAttempt


class OutboxEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutboxEvent
        fields = '__all__'


class NotificationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationAttempt
        fields = '__all__'
