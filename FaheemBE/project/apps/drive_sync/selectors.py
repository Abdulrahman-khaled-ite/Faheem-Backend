from typing import Optional
from django.db.models import QuerySet
from .models import EducationalMaterial, DriveFile, SourceRevision


def get_materials_by_course(course_name: str) -> QuerySet[EducationalMaterial]:
    """استرجاع المواد التعليمية لمقرر معين مصنفة."""
    return EducationalMaterial.objects.filter(
        course_name__icontains=course_name,
        is_published=True
    ).order_by('category', 'title')


def get_materials_by_year_and_category(
    study_year: int,
    department: str = 'عام',
    category: Optional[str] = None
) -> QuerySet[EducationalMaterial]:
    """استرجاع المواد التعليمية لسنة دراسية واختصاص وتصنيف محدد."""
    qs = EducationalMaterial.objects.filter(
        study_year=study_year,
        department=department,
        is_published=True
    )
    if category:
        qs = qs.filter(category=category)
    return qs.order_by('course_name', 'title')


def get_latest_source_revisions(limit: int = 20) -> QuerySet[SourceRevision]:
    """استرجاع أحدث إصدارات الملفات المرصودة من درايف."""
    return SourceRevision.objects.select_related('drive_file').order_by('-observed_at')[:limit]
