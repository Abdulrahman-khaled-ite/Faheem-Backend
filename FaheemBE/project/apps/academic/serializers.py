from rest_framework import serializers
from .models import (
    AcademicRecord,
    Course,
    AcademicYear,
    ExamSession,
    PublicationScope,
    CurrentGrade,
    GradeComponent,
    YearlyExamIdentity,
    DerivedAcademicState
)


class AcademicRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicRecord
        fields = ['id', 'official_name', 'normalized_name', 'university_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    study_year_display = serializers.CharField(source='get_original_study_year_display', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'original_study_year', 'study_year_display', 'department', 'semester']


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ['id', 'label', 'start_year']


class ExamSessionSerializer(serializers.ModelSerializer):
    academic_year_label = serializers.CharField(source='academic_year.label', read_only=True)

    class Meta:
        model = ExamSession
        fields = ['id', 'academic_year', 'academic_year_label', 'label', 'official_order']


class GradeComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeComponent
        fields = ['id', 'component_name', 'mark_value', 'evidence_ref']


class CurrentGradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='academic_record.official_name', read_only=True)
    course_name = serializers.CharField(source='scope.course.name', read_only=True)
    academic_year = serializers.CharField(source='scope.academic_year.label', read_only=True)
    session_label = serializers.CharField(source='scope.exam_session.label', read_only=True)
    components = GradeComponentSerializer(many=True, read_only=True)

    class Meta:
        model = CurrentGrade
        fields = [
            'id',
            'scope',
            'academic_record',
            'student_name',
            'course_name',
            'academic_year',
            'session_label',
            'final_mark',
            'absence_reason',
            'components',
            'updated_at'
        ]


class PublicationScopeSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    year_label = serializers.CharField(source='academic_year.label', read_only=True)
    session_label = serializers.CharField(source='exam_session.label', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = PublicationScope
        fields = [
            'id',
            'course',
            'course_name',
            'academic_year',
            'year_label',
            'exam_session',
            'session_label',
            'version',
            'fingerprint',
            'state',
            'state_display',
            'created_at',
            'updated_at'
        ]
