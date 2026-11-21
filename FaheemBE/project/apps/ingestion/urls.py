from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessingJobViewSet, IdentityMatchCandidateViewSet

router = DefaultRouter()
router.register(r'jobs', ProcessingJobViewSet, basename='processing-job')
router.register(r'candidates', IdentityMatchCandidateViewSet, basename='identity-candidate')

urlpatterns = [
    path('', include(router.urls)),
]
