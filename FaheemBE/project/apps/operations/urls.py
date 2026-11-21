from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OutboxEventViewSet, NotificationAttemptViewSet

router = DefaultRouter()
router.register(r'events', OutboxEventViewSet, basename='outbox-event')
router.register(r'notifications', NotificationAttemptViewSet, basename='notification-attempt')

urlpatterns = [
    path('', include(router.urls)),
]
