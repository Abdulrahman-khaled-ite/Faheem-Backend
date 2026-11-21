from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TelegramWebhookView, TelegramUserViewSet, StudentClaimRequestViewSet

router = DefaultRouter()
router.register(r'users', TelegramUserViewSet, basename='telegram-user')
router.register(r'claims', StudentClaimRequestViewSet, basename='student-claim')

urlpatterns = [
    path('webhook/', TelegramWebhookView.as_view(), name='telegram-webhook'),
    path('', include(router.urls)),
]
