import traceback

from rest_framework import viewsets
from rest_framework import parsers
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone

from .models import GCollection, GCollectionGPXFile, GcollectionShare, GCollectionWayPoint
from .serializers import GCollectionSerializer, GCollectionGPXFileSerializer, GCollectionWayPointSerializer
from .tasks import gc_gpx_file_process


class GCollectionPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        token = request.GET.get('token', None)
        if GcollectionShare.objects.filter(slug=token).filter(valid_until_date__gte=timezone.now()).count() > 0:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if type(obj) is GCollectionGPXFile:
            obj = obj.gcollection

        if request.user and request.user.is_authenticated:
            if obj.user == request.user:
                return True

        token = request.GET.get('token', None)
        if obj.shares.all().filter(slug=token).filter(valid_until_date__gte=timezone.now()).count() > 0:
            return True

        return False


class GCollectionGPXFilePermission(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            if obj.gcollection.user == request.user:
                return True

        return False


class GCollectionWayPointPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if obj.gcollection.user == request.user:
            return True
        return False


class GCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    serializer_class = GCollectionSerializer
    queryset = GCollection.objects.all()
    permission_classes = [GCollectionPermission]

    @action(detail=True, methods=['GET',], url_path="gpx_file/(?P<gpx_file_pk>[^/.]+)")
    def gpx_file(self, request, gpx_file_pk=None, pk=None):
        object = self.get_object()

        gpx_file = GCollectionGPXFile.objects.get(pk=gpx_file_pk, gcollection__pk=pk)
        serializer = GCollectionGPXFileSerializer(gpx_file, many=False)

        return Response(serializer.data)

    @action(detail=True, methods=['GET',])
    def waypoints(self, request, pk=None):
        pass


class GCollectionWaypointViewSet(viewsets.mixins.RetrieveModelMixin, viewsets.mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    serializer_class = GCollectionWayPointSerializer
    queryset = GCollectionWayPoint.objects.all()
    permission_classes = [GCollectionWayPointPermission]


class GCollectionGPXFileViewSet(viewsets.mixins.RetrieveModelMixin, viewsets.mixins.DestroyModelMixin, viewsets.GenericViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    serializer_class = GCollectionGPXFileSerializer
    queryset = GCollectionGPXFile.objects.all()
    permission_classes = [GCollectionGPXFilePermission]
    parser_classes = [parsers.MultiPartParser]

    def destroy(self, request, *args, **kwargs):
        gcollection = self.get_object().gcollection

        r = super().destroy(request, *args, **kwargs)

        try:
            gcollection.calculate_bounds()
        except Exception as e:
            print(traceback.print_exception(e))

        return r

    def create(self, request, *args, **kwargs):
        gcs = GCollection.objects.all().filter(user=request.user).filter(pk=request.data.get('gcollection', None))
        if gcs.count() != 1:
            return Response(status=400, data={'errors': ['Collection not found.']})

        if request.data.get('file', None) is None or request.data.get('file', None) == 'undefined':
            return Response(status=400, data={'errors': ['Please upload a file.']})

        gcollection = gcs.first()

        gpx_file = GCollectionGPXFile(
            gcollection=gcollection,
            name=request.data.get('name', None),
            file=request.data.get('file', None),
            date=request.data.get('date', None),
        )

        try:
            gpx_file.save()
        except ValidationError as e:
            print(traceback.print_exception(e))
            errors = []
            if 'file' in e.message_dict:
                errors.append('File is not valid or not uploaded.')
            if '__all__' in e.message_dict:
                for f in e.message_dict.get('__all__'):
                    if 'file_gcollection_name_unique' in f:
                        errors.append(f"Name '{gpx_file.name} is already used.")
                    else:
                        errors.append(f)

            return Response(status=400, data={'errors': errors})
        else:
            gc_gpx_file_process.delay(gc_gpx_file_pk=gpx_file.id)

        return Response({"id": gpx_file.id})
