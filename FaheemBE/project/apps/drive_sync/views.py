from rest_framework import viewsets, filters
from .models import DriveFile, SourceRevision, EducationalMaterial
from .serializers import DriveFileSerializer, SourceRevisionSerializer, EducationalMaterialSerializer


class DriveFileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriveFile.objects.all().order_by('-created_at')
    serializer_class = DriveFileSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'drive_path']


class SourceRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SourceRevision.objects.select_related('drive_file').all().order_by('-observed_at')
    serializer_class = SourceRevisionSerializer


class EducationalMaterialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EducationalMaterial.objects.select_related('drive_file').filter(is_published=True).order_by('study_year', 'course_name', 'category')
    serializer_class = EducationalMaterialSerializer
    filterset_fields = ['study_year', 'department', 'course_name', 'category']
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'course_name']
