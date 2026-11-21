from typing import Optional, List
from django.db.models import QuerySet, Q
from .models import (
    AcademicRecord,
    Course,
    AcademicYear,
    ExamSession,
    PublicationScope,
    CurrentGrade,
    YearlyExamIdentity,
    DerivedAcademicState,
    PublicationState
)


def get_academic_record_by_id(record_id: int) -> Optional[AcademicRecord]:
    """استرجاع السجل الأكاديمي بواسطة المعرف الداخلي."""
    return AcademicRecord.objects.filter(id=record_id).first()


def search_academic_records(query: str, limit: int = 10) -> QuerySet[AcademicRecord]:
    """البحث في السجلات الأكاديمية بالاسم أو الرقم الجامعي."""
    clean_query = query.strip()
    return AcademicRecord.objects.filter(
        Q(official_name__icontains=clean_query) |
        Q(normalized_name__icontains=clean_query) |
        Q(university_id__iexact=clean_query)
    )[:limit]


def get_yearly_identity(academic_year_id: int, exam_number: str) -> Optional[YearlyExamIdentity]:
    """جلب الهوية الامتحانية المثبتة لسنة ورقم امتحان محددين."""
    return YearlyExamIdentity.objects.select_related('academic_record', 'academic_year').filter(
        academic_year_id=academic_year_id,
        exam_number=str(exam_number).strip()
    ).first()


def get_student_current_grades(
    record_id: int,
    academic_year_id: Optional[int] = None,
    course_id: Optional[int] = None
) -> QuerySet[CurrentGrade]:
    """
    جلب كافة العلامات الحالية المنشورة رسمياً لطالب معين مع تفاصيل المقرر والنطاق.
    """
    qs = CurrentGrade.objects.select_related(
        'scope',
        'scope__course',
        'scope__academic_year',
        'scope__exam_session',
        'provenance'
    ).prefetch_related('components').filter(
        academic_record_id=record_id,
        scope__state=PublicationState.PUBLISHED
    )

    if academic_year_id:
        qs = qs.filter(scope__academic_year_id=academic_year_id)
    if course_id:
        qs = qs.filter(scope__course_id=course_id)

    return qs.order_by('-scope__academic_year__start_year', 'scope__course__name')


def list_courses(study_year: Optional[int] = None, department: Optional[str] = None) -> QuerySet[Course]:
    """استرجاع المقررات الدراسية مع إمكانية التصفية بالسنة والاختصاص."""
    qs = Course.objects.all()
    if study_year:
        qs = qs.filter(original_study_year=study_year)
    if department:
        qs = qs.filter(department=department)
    return qs.order_by('original_study_year', 'semester', 'name')


def get_publication_scope(
    course_id: int,
    academic_year_id: int,
    exam_session_id: int
) -> Optional[PublicationScope]:
    """جلب نطاق النشر المحدد."""
    return PublicationScope.objects.filter(
        course_id=course_id,
        academic_year_id=academic_year_id,
        exam_session_id=exam_session_id
    ).first()
