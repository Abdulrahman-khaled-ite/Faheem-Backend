from django.contrib import admin
from .models import (
    AcademicRecord,
    AcademicYear,
    YearlyExamIdentity,
    Course,
    ExamSession,
    PublicationScope,
    PublicationVersion,
    CurrentGrade,
    GradeComponent,
    GradeProvenance,
    DerivedAcademicState
)


@admin.register(AcademicRecord)
class AcademicRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'official_name', 'university_id', 'created_at')
    search_fields = ('official_name', 'normalized_name', 'university_id')
    ordering = ('id',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'original_study_year', 'department', 'semester', 'code')
    list_filter = ('original_study_year', 'department', 'semester')
    search_fields = ('name', 'code')


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('label', 'start_year')
    ordering = ('-start_year',)


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'label', 'official_order')
    list_filter = ('academic_year',)


@admin.register(YearlyExamIdentity)
class YearlyExamIdentityAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'exam_number', 'academic_record', 'verified_at')
    list_filter = ('academic_year',)
    search_fields = ('exam_number', 'academic_record__official_name')


@admin.register(PublicationScope)
class PublicationScopeAdmin(admin.ModelAdmin):
    list_display = ('course', 'academic_year', 'exam_session', 'version', 'state', 'updated_at')
    list_filter = ('state', 'academic_year', 'course__original_study_year')
    search_fields = ('course__name',)


class GradeComponentInline(admin.TabularInline):
    model = GradeComponent
    extra = 0


@admin.register(CurrentGrade)
class CurrentGradeAdmin(admin.ModelAdmin):
    list_display = ('academic_record', 'course_name', 'academic_year', 'final_mark', 'absence_reason', 'updated_at')
    list_filter = ('scope__academic_year', 'scope__course__original_study_year')
    search_fields = ('academic_record__official_name', 'scope__course__name')
    inlines = [GradeComponentInline]

    def course_name(self, obj):
        return obj.scope.course.name

    def academic_year(self, obj):
        return obj.scope.academic_year.label


@admin.register(GradeProvenance)
class GradeProvenanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_revision', 'source_row_ref', 'decision_reason', 'created_at')
    search_fields = ('source_row_ref', 'decision_reason')
