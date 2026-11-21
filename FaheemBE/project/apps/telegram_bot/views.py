from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, viewsets
from django.conf import settings
from .models import TelegramUser, StudentClaimRequest
from .serializers import TelegramUserSerializer, StudentClaimRequestSerializer
from .services import TelegramBotService


class TelegramWebhookView(APIView):
    """
    نقطة استقبال الـ Webhook الرسمية من سيرفرات Telegram:
    - التحقق من الـ Webhook Secret Header.
    - تمرير التحديث لمحرك البوت لمعالجته بأسلوب Idempotent.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        expected_secret = settings.FAHEEM_CONFIG.get('TELEGRAM_WEBHOOK_SECRET')
        received_secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')

        if expected_secret and received_secret != expected_secret:
            return Response({'error': 'Unauthorized webhook secret'}, status=status.HTTP_403_FORBIDDEN)

        bot_service = TelegramBotService()
        result = bot_service.handle_webhook_update(request.data)
        return Response(result, status=status.HTTP_200_OK)


class TelegramUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TelegramUser.objects.select_related('linked_record').all().order_by('-created_at')
    serializer_class = TelegramUserSerializer
    filterset_fields = ['is_verified', 'role']


class StudentClaimRequestViewSet(viewsets.ModelViewSet):
    queryset = StudentClaimRequest.objects.select_related('telegram_user', 'academic_record').all().order_by('-created_at')
    serializer_class = StudentClaimRequestSerializer
    filterset_fields = ['status']
