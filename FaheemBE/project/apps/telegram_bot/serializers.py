from rest_framework import serializers
from .models import TelegramUser, StudentClaimRequest, InteractionLog


class TelegramUserSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='linked_record.official_name', read_only=True)

    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'username', 'first_name', 'last_name', 'linked_record', 'student_name', 'role', 'is_verified', 'created_at']


class StudentClaimRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='telegram_user.username', read_only=True)
    student_name = serializers.CharField(source='academic_record.official_name', read_only=True)

    class Meta:
        model = StudentClaimRequest
        fields = ['id', 'telegram_user', 'username', 'academic_record', 'student_name', 'claimed_exam_number', 'claimed_academic_year', 'status', 'created_at']
