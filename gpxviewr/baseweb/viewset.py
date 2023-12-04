from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    GPXFile,
)


class GPXFileViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['GET',])
    def job_status(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        return Response({
            'job_status_name': gpx_file.get_job_status(),
            'finished': gpx_file.job_is_finished(),
        })

    @action(detail=True, methods=['GET',])
    def geojson(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        return Response(gpx_file.geojson_polyline())
