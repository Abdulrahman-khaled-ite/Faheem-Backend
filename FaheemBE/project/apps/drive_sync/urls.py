from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DriveFileViewSet, SourceRevisionViewSet, EducationalMaterialViewSet

router = DefaultRouter()
router.register(r'files', DriveFileViewSet, basename='drive-file')
router.register(r'revisions', SourceRevisionViewSet, basename='source-revision')
router.register(r'materials', EducationalMaterialViewSet, basename='educational-material')

urlpatterns = [
    path('', include(router.urls)),
]
