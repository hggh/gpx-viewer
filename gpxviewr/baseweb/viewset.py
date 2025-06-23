from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

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
from .serializers import GPXWayPointTypeSerializer, GPXFileSerializer


class GPXWayPointTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GPXWayPointType.objects.all()
    serializer_class = GPXWayPointTypeSerializer


class GPXFilePermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if type(obj) is GPXFile:
            if obj.perm_public_available is False:
                if request.user.is_authenticated and obj.user == request.user:
                    return True
                else:
                    return False
            else:
                return True
        else:
            print(f"{obj} with {type(obj)} not kown")
            return False


class GPXFileViewSet(viewsets.mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    queryset = GPXFile.objects.all()
    serializer_class = GPXFileSerializer
    permission_classes = [GPXFilePermission]
    lookup_field = 'slug'

    @action(detail=True, methods=['POST',])
    def job_status(self, request, slug=None):
        gpx_file = self.get_object()

        return Response({
            'job_status_name': gpx_file.get_job_status(),
            'finished': gpx_file.job_is_finished(),
        })

    @action(detail=True, methods=['GET',])
    def json(self, request, slug=None):
        gpx_file = self.get_object()

        json = gpx_file.get_json_data()
        if json is None:
            return Response({}, status=404)

        return Response(json)

    @action(detail=True, methods=['POST',])
    def geojson_track_to_waypoint(self, request, slug=None):
        gpx_file = self.get_object()

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
    def user_segment_splits(self, request, slug=None):
        gpx_file = self.get_object()

        return Response(gpx_file.get_user_segment_splits(segment_pk=request.data.get('segment_pk', None)))

    @action(detail=True, methods=['POST',])
    def user_segment_split(self, request, slug=None):
        splitted_data = request.data.get('splitted_data', [])
        segment_pk = request.data.get('segment_pk', None)
        if segment_pk is None:
            return Response({"segment_pk missing"}, status=403)
        gpx_file = self.get_object()

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

    @action(detail=True, methods=['POST',], url_path="waypoint_bookmark_toggle/(?P<waypoint_pk>[^/.]+)")
    def waypoint_bookmark_toggle(self, request, waypoint_pk=None, slug=None):
        gpx_file = self.get_object()

        w = GPXTrackWayPoint.objects.get(pk=waypoint_pk, gpx_file=gpx_file)
        w.bookmark = not w.bookmark
        w.save(update_fields=['bookmark'])

        return Response({'bookmark': w.bookmark})

    @action(detail=True, methods=['POST',])
    def waypoints(self, request, slug=None):
        gpx_file = self.get_object()

        waypoints_data = []
        for w in gpx_file.waypoints.all():
            waypoints_data.append(w.get_json_data())

        waypoint_types_data = []
        for wt in GPXWayPointType.objects.all():
            waypoint_types_data.append(wt.get_json_data())

        return Response({"waypoints": waypoints_data, "waypoint_types": waypoint_types_data})
