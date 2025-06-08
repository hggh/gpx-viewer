from rest_framework import serializers

from .models import GCollection, GCollectionGPXFile, GCollectionWayPoint, GCollectionWayPointType


class GCollectionWayPointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GCollectionWayPointType
        fields = ['name', 'image_name',]


class NestedGCollectionWayPointSerializer(serializers.ModelSerializer):
    waypoint_type = GCollectionWayPointTypeSerializer()
    location = serializers.JSONField(source='get_location_leaflet')

    class Meta:
        model = GCollectionWayPoint
        fields = ['id', 'name', 'location', 'waypoint_type',]


class GCollectionSerializer(serializers.ModelSerializer):
    bounds = serializers.JSONField(source='get_leaflet_bounds')
    waypoints = NestedGCollectionWayPointSerializer(many=True)

    class Meta:
        model = GCollection
        fields = ['id', 'name', 'bounds', 'gpx_files', 'waypoints',]


class GCollectionGPXFileSerializer(serializers.ModelSerializer):
    json = serializers.JSONField()

    class Meta:
        model = GCollectionGPXFile
        fields = ['id', 'name', 'date', 'job_status', 'json', 'distance', 'ascent', 'descent']


class GCollectionWayPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GCollectionWayPoint
        fields = ['gcollection', 'name', 'waypoint_type', 'location',]
