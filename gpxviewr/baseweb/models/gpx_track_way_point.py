import phonenumbers

from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point

from django_extensions.db.models import TimeStampedModel


class GPXTrackWayPoint(TimeStampedModel):
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='waypoints')
    waypoint_type = models.ForeignKey("GPXWayPointType", on_delete=models.CASCADE, related_name='waypoints')
    name = models.CharField(max_length=100, null=False, blank=True)
    tags = models.JSONField(default=dict)
    hidden = models.BooleanField(null=False, blank=False, default=False)

    location = models.PointField(default=Point(0.0, 0.0), db_index=True)
    track_segment_point_nearby = models.ForeignKey("GPXTrackSegmentPoint", related_name='waypoints', on_delete=models.CASCADE)

    class Meta:
        ordering = ['track_segment_point_nearby__pk', 'id']

    def get_json_data(self) -> dict:
        # FIXME: als geoJSON!?
        data = {
            "id": self.pk,
            "has_gpx_track_to": self.has_gpx_track_to(),
            "lat": self.location.x,
            "lon": self.location.y,
            "class_name": self.get_marker_css_name(),
            "url": self.get_url(),
            "hidden": self.hidden,
            "name": self.name,
            "waypoint_type": {
                "name": self.waypoint_type.name,
                "html_id": self.waypoint_type.html_id(),
                "marker_image_path": self.waypoint_type.marker_image_path(),

            }
        }
        return data

    def has_gpx_track_to(self) -> bool:
        try:
            if self.track_to_waypoint:
                return True
        except ObjectDoesNotExist:
            pass
        return False

    def get_marker_css_name(self) -> str:
        if self.is_camping_site() is True and self.get_url():
            return 'marker_camping_with_url'
        return 'marker_default'

    def get_tags(self) -> dict:
        tags = self.tags
        tags.pop('contact:website', None)
        tags.pop('contact:phone', None)
        tags.pop('phone', None)
        tags.pop('website', None)
        tags.pop('url', None)
        tags.pop('name', None)

        return tags

    def track_segment_distance(self):
        if self.track_segment_point_nearby and self.track_segment_point_nearby.distance:
            value = int(self.track_segment_point_nearby.distance / 1000)
            if value == 0:
                return 1
            return value
        return None

    def user_segment_split_distance(self):
        if self.gpx_file.user_segments.all() and self.track_segment_point_nearby and self.track_segment_point_nearby.distance:
            split = self.gpx_file.user_segments.all().filter(point_start__number__lte=self.track_segment_point_nearby.number).order_by('point_start__number').last()
            if split:
                value = int((self.track_segment_point_nearby.distance - split.point_start.distance) / 1000)
                if value == 0:
                    return 1
                return value
        return None

    def get_phone(self) -> str | None:
        if self.tags.get('phone', None):
            try:
                phonenumbers.parse(self.tags.get('phone'), None)
                return self.tags.get('phone')
            except Exception as e:
                pass

        if self.tags.get('contact:phone', None):
            try:
                phonenumbers.parse(self.tags.get('contact:phone'), None)
                return self.tags.get('contact:phone')
            except Exception as e:
                pass
        return None

    def get_url(self) -> str:
        if self.tags.get('contact:website', None):
            return self.tags.get('contact:website')

        if self.tags.get('url', None):
            return self.tags.get('url', None)

        return self.tags.get('website', None)

    def is_camping_site(self) -> bool:
        if self.waypoint_type.osm_value == 'camp_site':
            return True
        return False

    def is_hotel(self) -> bool:
        if 'hotel' in self.waypoint_type.osm_value:
            return True
        return False
