from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from django.core.exceptions import ObjectDoesNotExist

from .models import (
    GPXFile,
    GPXWayPointType,
    GPXTrackWayPoint,
    GPXFileUserSegmentSplit,
    GPXWayPointType,
    GPXTrackSegment,
    GPXTrackSegmentPoint,
)
from .serializers import GPXWayPointTypeSerializer


class GPXWayPointTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GPXWayPointType.objects.all()
    serializer_class = GPXWayPointTypeSerializer


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

        return Response(gpx_file.get_user_segment_splits(segment_pk=request.data.get('segment_pk', None)))

    @action(detail=True, methods=['POST',])
    def user_segment_split(self, request, pk=None):
        splitted_data = request.data.get('splitted_data', [])
        segment_pk = request.data.get('segment_pk', None)
        if segment_pk is None:
            return Response({"segment_pk missing"}, status=403)
        gpx_file = GPXFile.objects.get(slug=pk)

        segment = GPXTrackSegment.objects.get(pk=segment_pk, track__gpx_file=gpx_file)

        # we delete all UserSegmentSplit Point and recreate it
        gpx_file.user_segments.all().filter(point_start__segment=segment).delete()

        user_split_number = 1
        update_splits = []
        for i in range(len(splitted_data)):
            element = splitted_data[i]

            point_start = GPXTrackSegmentPoint.objects.get(number=element.get('point_number'), segment=segment)
            try:
                element_next = splitted_data[i+ 1]
                point_end = GPXTrackSegmentPoint.objects.get(number=element_next.get('point_number'), segment=segment)
            except IndexError:
                element_next = None
                point_end = segment.points.all().last()
            print(f"Next element {element_next}")

            u = GPXFileUserSegmentSplit(
                name=f"Track {user_split_number}",
                gpx_file=gpx_file,
                point_start=point_start,
                point_end=point_end,
            )
            u.save()
            update_splits.append(u)
            user_split_number += 1

        if len(update_splits) > 0:
            GPXFileUserSegmentSplit.update_segments(update_splits, gpx_file=gpx_file, segment_pk=segment_pk)

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
