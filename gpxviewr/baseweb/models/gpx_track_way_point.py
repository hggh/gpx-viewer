import phonenumbers
import gpxpy
from xml.etree import ElementTree

from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.geos import Point
from geopy import distance as geopy_distance

from django_extensions.db.models import TimeStampedModel


class GPXTrackWayPoint(TimeStampedModel):
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='waypoints')
    waypoint_type = models.ForeignKey("GPXWayPointType", on_delete=models.CASCADE, related_name='waypoints')
    name = models.CharField(max_length=100, null=False, blank=True)
    tags = models.JSONField(default=dict)
    hidden = models.BooleanField(null=False, blank=False, default=False)
    bookmark = models.BooleanField(null=False, default=False, blank=False, db_index=True)

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

    def get_air_distance_from_track(self) -> str:
        d = geopy_distance.distance((self.track_segment_point_nearby.location.x, self.track_segment_point_nearby.location.y), (self.location.x, self.location.y))
        if d.m > 1500:
            return f"{int(d.km)} km"
        return f"{int(d.m)} m"

    def has_gpx_track_to(self) -> bool:
        try:
            if self.track_to_waypoint:
                return True
        except ObjectDoesNotExist:
            pass
        return False

    def get_marker_css_name(self) -> str:
        if self.is_camping_site() is True and self.tags.get('permanent_camping', '') == 'only':
            return 'marker_camping_red'
        elif self.is_camping_site() is True and self.tags.get('group_only', '') == 'yes':
            return 'marker_camping_red'
        elif self.is_camping_site() is True and self.tags.get('tents', '') == 'no':
            return 'marker_camping_red'
        elif self.is_camping_site() is True and self.get_url():
            return 'marker_camping_with_url'
        elif self.is_ebike_charging_station() is True and self.tags.get('access', '') == 'yes':
            return 'marker_ebike_charging_access_yes'
        else:
            return 'marker_default'

    def has_feature_css_toilets(self):
        if self.tags.get('toilets', None) is None:
            return ''

        if self.tags.get('toilets', None) == 'yes':
            return 'osm_feature_toilets'

        return 'osm_feature_toilets_no'

    def has_feature_css_caravans(self):
        if self.tags.get('caravans', None) is None:
            return ''

        if self.tags.get('caravans', None) == 'yes':
            return 'osm_feature_caravans'

        return 'osm_feature_caravans_no'

    def has_feature_css_shower(self):
        if self.tags.get('shower', None) is None:
            return ''

        if self.tags.get('shower', None) in ['yes', 'cold', 'hot']:
            return 'osm_feature_shower'

        return 'osm_feature_shower_no'

    def has_feature_css_tents(self):
        if self.tags.get('tents', None) is None:
            return ''

        if self.tags.get('tents', None) == 'yes':
            return 'osm_feature_tents'

        return 'osm_feature_tents_no'

    def has_feature_css_cabins(self):
        if self.tags.get('cabins', None) is None:
            return ''

        if self.tags.get('cabins', None) == 'yes':
            return 'osm_feature_cabins'

        return 'osm_feature_cabins_no'

    def has_feature_css_drinking_water(self):
        if self.tags.get('drinking_water', None) is None:
            return ''

        if self.tags.get('drinking_water', None) == 'yes':
            return 'osm_feature_drinking_water'

        return 'osm_feature_drinking_water_no'

    def has_feature_css_openfire(self):
        if self.tags.get('openfire', None) is None:
            return ''

        if self.tags.get('openfire', None) == 'yes':
            return 'osm_feature_openfire'

        return 'osm_feature_openfire_no'

    def has_feature_css_fee(self):
        if self.tags.get('fee', None) is None:
            return ''

        if self.tags.get('fee', None) == 'yes':
            return 'osm_feature_fee'

        return 'osm_feature_fee_no'

    def get_tags(self) -> dict:
        tags = self.tags
        tags.pop('contact:website', None)
        tags.pop('contact:phone', None)
        tags.pop('phone', None)
        tags.pop('website', None)
        tags.pop('url', None)
        tags.pop('name', None)
        tags.pop('toilets', None)
        tags.pop('tourism', None)
        tags.pop('caravans', None)
        tags.pop('shower', None)
        tags.pop('tents', None)
        tags.pop('cabins', None)
        tags.pop('drinking_water', None)
        tags.pop('openfire', None)
        tags.pop('fee', None)

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

    def generate_gpx_waypoint(self, mode='normal'):
        if not self.name:
            name = self.waypoint_type.name
        else:
            name= self.name

        w = gpxpy.gpx.GPXWaypoint(
            symbol=self.waypoint_type.gpx_sym_name,
            name=name,
            type=self.waypoint_type.gpx_type_name,
        )
        if self.get_url():
            w.link = self.get_url()
        if self.get_phone():
            w.comment = self.get_phone()

        if mode == 'garmin':
            w.latitude = self.track_segment_point_nearby.location.x
            w.longitude = self.track_segment_point_nearby.location.y
        else:
            w.latitude = self.location.x
            w.longitude = self.location.y

        w.description = "away: " + self.get_air_distance_from_track()

        osmand_icon = ElementTree.Element("osmand:icon")
        osmand_icon.text = self.waypoint_type.osmand_icon
        w.extensions.append(osmand_icon)

        return w

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

    def get_url(self) -> None | str:
        if self.tags.get('contact:website', None):
            return self.tags.get('contact:website')

        if self.tags.get('url', None):
            return self.tags.get('url', None)

        return self.tags.get('website', None)

    def is_ebike_charging_station(self) -> bool:
        if self.waypoint_type.osm_value == 'charging_station':
            return True
        return False

    def is_camping_site(self) -> bool:
        if self.waypoint_type.osm_value == 'camp_site':
            return True
        return False

    def is_hotel(self) -> bool:
        if 'hotel' in self.waypoint_type.osm_value:
            return True
        return False
