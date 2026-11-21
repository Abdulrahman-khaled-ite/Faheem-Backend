from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ProcessingJob, IdentityMatchCandidate
from .serializers import ProcessingJobSerializer, IdentityMatchCandidateSerializer
from .services import IngestionPipelineService


class ProcessingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProcessingJob.objects.select_related('source_revision__drive_file').all().order_by('-created_at')
    serializer_class = ProcessingJobSerializer
    filterset_fields = ['state']

    @action(detail=True, methods=['post'])
    def trigger(self, request, pk=None):
        """إعادة تشغيل مهمة معالجة يدوياً."""
        job = self.get_object()
        processed_job = IngestionPipelineService.execute_job(job)
        return Response({'status': processed_job.state, 'reason': processed_job.reason})

    @action(detail=True, methods=['get'])
    def candidates(self, request, pk=None):
        """عرض كافة المرشحين المستخرجين للمهمة."""
        candidates = IdentityMatchCandidate.objects.filter(job_id=pk).order_by('id')
        serializer = IdentityMatchCandidateSerializer(candidates, many=True)
        return Response(serializer.data)


class IdentityMatchCandidateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IdentityMatchCandidate.objects.select_related('candidate_record').all()
    serializer_class = IdentityMatchCandidateSerializer
    filterset_fields = ['job', 'status']
