from rest_framework import serializers
from .models import ProcessingJob, ProcessingAttempt, ProcessingArtifact, IdentityMatchCandidate


class ProcessingJobSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(source='source_revision.drive_file.name', read_only=True)

    class Meta:
        model = ProcessingJob
        fields = ['id', 'source_revision', 'file_name', 'state', 'reason', 'correlation_id', 'created_at', 'updated_at']


class IdentityMatchCandidateSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source='candidate_record.official_name', read_only=True)

    class Meta:
        model = IdentityMatchCandidate
        fields = [
            'id',
            'job',
            'row_ref',
            'raw_name',
            'normalized_name',
            'exam_number',
            'extracted_mark',
            'candidate_record',
            'candidate_name',
            'score',
            'status'
        ]
