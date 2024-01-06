from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from django.core.exceptions import ObjectDoesNotExist

from .models import (
    GPXFile,
    GPXWayPointType,
    GPXTrackWayPoint,
    GPXFileUserSegmentSplit,
)


class GPXFileViewSet(viewsets.ViewSet):
    @action(detail=True, methods=['POST',])
    def job_status(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        return Response({
            'job_status_name': gpx_file.get_job_status(),
            'finished': gpx_file.job_is_finished(),
        })

    @action(detail=True, methods=['POST',])
    def geojson(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        data = gpx_file.geojson_polyline()

        if data is None:
            return Response({}, status=404)

        return Response(data)

    @action(detail=True, methods=['POST',])
    def geojson_track_to_waypoint(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        waypoint_pk = request.data.get('waypoint_pk', None)

        if waypoint_pk is None:
            return Response({'error_msg': 'waypoint_pk missing'}, status=500)

        try:
            waypoint = GPXTrackWayPoint.objects.get(gpx_file=gpx_file, pk=waypoint_pk)
        except GPXTrackWayPoint.DoesNotExist as e:
            return Response({}, status=404)

        try:
            return Response(waypoint.track_to_waypoint.get_geojson())
        except ObjectDoesNotExist:
            return Response({}, status=404)

    @action(detail=True, methods=['POST',])
    def user_segment_splits(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        return Response({"user_segment_splits": gpx_file.get_user_segment_splits()})

    @action(detail=True, methods=['POST',])
    def user_segment_split(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        segment = GPXFileUserSegmentSplit.add_segment(gpx_file=gpx_file, start=request.data.get('start'), end=request.data.get('end'))

        return Response({})

    @action(detail=True, methods=['POST',])
    def waypoints(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        waypoints_data = []
        for w in gpx_file.waypoints.all():
            waypoints_data.append(w.get_json_data())

        waypoint_types_data = []
        for wt in GPXWayPointType.objects.all():
            waypoint_types_data.append(wt.get_json_data())

        return Response({"waypoints": waypoints_data, "waypoint_types": waypoint_types_data})
