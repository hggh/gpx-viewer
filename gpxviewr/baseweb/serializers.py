from rest_framework import serializers

from baseweb.models import GPXWayPointType


class GPXWayPointTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPXWayPointType
        fields = ['id', 'name', 'html_id', 'around', 'around_duplicate', 'checked',]
