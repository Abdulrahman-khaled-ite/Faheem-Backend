from rest_framework import serializers
from .models import DriveFile, SourceRevision, EducationalMaterial


class DriveFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveFile
        fields = '__all__'


class SourceRevisionSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='drive_file.name', read_only=True)

    class Meta:
        model = SourceRevision
        fields = ['id', 'drive_file', 'file_name', 'pdf_digest', 'file_size_bytes', 'observed_at']


class EducationalMaterialSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='drive_file.name', read_only=True)
    web_link = serializers.CharField(source='drive_file.web_view_link', read_only=True)

    class Meta:
        model = EducationalMaterial
        fields = [
            'id',
            'study_year',
            'department',
            'course_name',
            'category',
            'title',
            'file_name',
            'web_link',
            'is_published',
            'created_at'
        ]
