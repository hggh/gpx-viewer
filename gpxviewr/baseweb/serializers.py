from rest_framework import serializers

from baseweb.models import GPXWayPointType, GPXFile


class GPXWayPointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPXWayPointType
        fields = ['id', 'name', 'html_id', 'around', 'around_duplicate', 'checked',]


class GPXFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPXFile
        fields = ['id', 'name']
