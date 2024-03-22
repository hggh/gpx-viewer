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

    @action(detail=True, methods=['GET',])
    def json(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        json = gpx_file.get_json_data()
        if json is None:
            return Response({}, status=404)

        return Response(json)

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

        return Response(gpx_file.get_user_segment_splits())

    @action(detail=True, methods=['POST',])
    def user_segment_split(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        status = GPXFileUserSegmentSplit.add_segment(
            gpx_file=gpx_file,
            start=request.data.get('start'),
            end=request.data.get('end'),
            name=request.data.get('name', ''),
        )

        return Response(status)

    @action(detail=True, methods=['POST',])
    def user_segment_split_delete(self, request, pk=None):
        gpx_file = GPXFile.objects.get(slug=pk)

        GPXFileUserSegmentSplit.objects.filter(
            gpx_file=gpx_file,
            pk=request.data.get('user_segment_pk')
        ).delete()

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
