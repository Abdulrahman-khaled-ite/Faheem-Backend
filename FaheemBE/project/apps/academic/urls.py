from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AcademicRecordViewSet,
    CourseViewSet,
    AcademicYearViewSet,
    PublicationScopeViewSet,
    CurrentGradeViewSet
)

router = DefaultRouter()
router.register(r'records', AcademicRecordViewSet, basename='academic-record')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'years', AcademicYearViewSet, basename='academic-year')
router.register(r'scopes', PublicationScopeViewSet, basename='publication-scope')
router.register(r'grades', CurrentGradeViewSet, basename='current-grade')

urlpatterns = [
    path('', include(router.urls)),
]
