from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    AcademicRecord,
    Course,
    AcademicYear,
    ExamSession,
    PublicationScope,
    CurrentGrade
)
from .serializers import (
    AcademicRecordSerializer,
    CourseSerializer,
    AcademicYearSerializer,
    ExamSessionSerializer,
    PublicationScopeSerializer,
    CurrentGradeSerializer
)
from .selectors import (
    get_student_current_grades,
    search_academic_records
)


class AcademicRecordViewSet(viewsets.ModelViewSet):
    """إدارة واستعراض السجلات الأكاديمية للطلاب."""
    queryset = AcademicRecord.objects.all().order_by('id')
    serializer_class = AcademicRecordSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['official_name', 'normalized_name', 'university_id']

    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        """عرض كافة العلامات المنشورة للطالب المحدد."""
        grades_qs = get_student_current_grades(record_id=pk)
        serializer = CurrentGradeSerializer(grades_qs, many=True)
        return Response(serializer.data)


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """استعراض المقررات الدراسية."""
    queryset = Course.objects.all().order_by('original_study_year', 'semester', 'name')
    serializer_class = CourseSerializer
    filterset_fields = ['original_study_year', 'department', 'semester']


class AcademicYearViewSet(viewsets.ReadOnlyModelViewSet):
    """استعراض السنوات الأكاديمية."""
    queryset = AcademicYear.objects.all().order_by('-start_year')
    serializer_class = AcademicYearSerializer


class PublicationScopeViewSet(viewsets.ReadOnlyModelViewSet):
    """استعراض نطاقات النشر وحالاتها."""
    queryset = PublicationScope.objects.select_related('course', 'academic_year', 'exam_session').all()
    serializer_class = PublicationScopeSerializer
    filterset_fields = ['course', 'academic_year', 'exam_session', 'state']


class CurrentGradeViewSet(viewsets.ReadOnlyModelViewSet):
    """استعراض العلامات الحالية المنشورة."""
    queryset = CurrentGrade.objects.select_related(
        'scope', 'scope__course', 'scope__academic_year', 'scope__exam_session', 'academic_record'
    ).prefetch_related('components').all()
    serializer_class = CurrentGradeSerializer
    filterset_fields = ['scope', 'academic_record']
