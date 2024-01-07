from pathlib import Path
import secrets
import time
import os
import geojson
from geopy import distance as geopy_distance
from datetime import timedelta

from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models.functions import Distance as FDistance
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.db.models.signals import post_delete
from django.db.models import Sum
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel

import overpy

import numpy
import pandas
from gpx import GPX, Waypoint, Track
from gpx.track_segment import TrackSegment
from gpx.waypoint import Link


fs = FileSystemStorage(location=settings.LOCAL_STORAGE_DIRECTORY)


def generate_slug_token():
    return secrets.token_urlsafe(30)


def generate_default_delete_after_date():
    return (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d')


class GPXFile(TimeStampedModel):
    job_status_fields = {
        1: 'uploaded',
        2: 'gpx_track_loading',
        3: 'osm_query',
        4: 'finished',
        5: 'error',
    }
    line_colors = [
        '#ff0066',
        '#1f1fbf',
        '#3ef0fb',
        '#502968',
        '#448137',
    ]

    slug = models.SlugField(default=generate_slug_token, editable=False, max_length=50)
    name = models.CharField(max_length=100, null=False, blank=False)
    wpt_options = models.JSONField(default=dict)
    job_status = models.IntegerField(default=1, null=False)
    delete_after = models.DateField(null=False, blank=False)

    file = models.FileField(storage=fs, upload_to="gpx_track/%Y/%m/%d/")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name', '-created',]

    def get_absolute_url(self) -> str:
        return reverse("gpx-file-detail", kwargs={"slug": self.slug})

    def save(self, **kwargs):
        if self.name is None or self.name == '':
            self.name = self.file.name.replace('.gpx', '')

        return super().save(**kwargs)

    def get_job_status(self) -> str:
        return self.job_status_fields.get(self.job_status, 'unkown')

    def job_is_finished(self) -> bool:
        if self.get_job_status() == 'finished':
            return True
        return False

    def get_all_segments_primary_keys(self):
        return GPXTrackSegment.objects.all().filter(track__in=self.tracks.all().values_list('pk'))

    def get_waypoint_types(self) -> list:
        data = []
        for wtp in GPXWayPointType.objects.all():
            o = self.wpt_options.get(wtp.name, {})

            if o.get('enabled', False) is True:
                data.append(wtp)

        return data

    def get_waypoint_types_with_entries(self):
        wtps = []
        for wtp in GPXWayPointType.objects.all():
            wtps.append({
                'object': wtp,
                'waypoints': self.waypoints.all().filter(waypoint_type=wtp),
            })
        return wtps

    def generate_download_gpx_file(self, options) -> str:
        gpx = GPX()
        gpx.creator = 'GPX Tools by hggh'
        waypoints = []

        for w in self.waypoints.all().filter(waypoint_type__in=options).filter(hidden=False):
            wp = Waypoint()
            wp.lat = w.location.x
            wp.lon = w.location.y
            wp.name = w.name
            wp.sym = w.waypoint_type.gpx_sym_name

            if w.get_url():
                wp_link = Link()
                wp_link.href = w.get_url()
                wp_link.text = w.get_url()
                wp.links = [wp_link]

            waypoints.append(wp)

        gpx.waypoints = waypoints

        return gpx.to_string()

    def get_user_segment_splits(self) -> list:
        data = []

        for s in self.user_segments.all():
            segment = {
                "name": s.name,
                "start": {
                    "lat": float(s.point_start.location.x),
                    "lon": float(s.point_start.location.y),
                },
                "end": {
                    "lat": float(s.point_end.location.x),
                    "lon": float(s.point_end.location.y),
                }
            }
            data.append(segment)

        return data

    def geojson_polyline(self, refresh=False):
        filename = os.path.join(settings.LOCAL_GEOJSON_TEMP_DIRECTORY, f"{self.slug}.geojson")

        if os.path.exists(filename) and refresh is False:
            return geojson.loads(Path(filename).read_text())

        if self.job_status < 3:
            return None

        color_int = 0
        fc = geojson.FeatureCollection(features=[])
        for track in self.tracks.all():
            for segment in track.segments.all():
                line = geojson.LineString()

                for point in segment.points.all():
                    line.coordinates.append([float(point.location.y), float(point.location.x)])

                fc.features.append(geojson.Feature(
                    geometry=line,
                    properties={
                        'color': self.line_colors[color_int],
                        'weight': 3,
                        'opacity': 0.7,
                        'segment_pk': segment.pk,
                    })
                )

                color_int += 1
                if color_int >= len(self.line_colors):
                    color_int = 0
                del line

        Path(filename).write_text(geojson.dumps(fc))

        return fc

    def generate_waypoints(self, point_type, around_meters=None, around_duplicate=0) -> None:
        if around_meters is None:
            around_meters = point_type.around

        gpxfile = GPX.from_file(self.file.path)

        for track in gpxfile.tracks:
            for segment in track.trksegs:
                points = []
                curr = 0

                for point in segment.trkpts:
                    points.append((point.lat, point.lon))
                    curr += 1

                    if curr == 2000:
                        self.query_data_osm(
                            points=points,
                            around_meters=around_meters,
                            point_type=point_type,
                            around_duplicate=around_duplicate,
                        )
                        time.sleep(1)
                        points = []
                        curr = 0

                self.query_data_osm(
                    points=points,
                    around_meters=around_meters,
                    point_type=point_type,
                    around_duplicate=around_duplicate,
                )
                time.sleep(1)

    def query_data_osm(self, points, around_meters, point_type, around_duplicate) -> None:
        from .tasks import gpx_waypoint_find_route_from_track

        track_points = pandas.DataFrame(points, columns=["lat", "lon"])
        track_latlong_flatten = ",".join(track_points.to_numpy().flatten().astype("str"))

        api = overpy.Overpass()
        overpass_query = f"""
            [out:json][timeout: 500];
            (
                nwr["{point_type.osm_name}" {point_type.osm_query_type} "{point_type.osm_value}"](around:{around_meters},{track_latlong_flatten});
            );
            out center qt;
        """
        result = api.query(overpass_query)

        for node in result.get_nodes():
            wp = GPXTrackWayPoint(
                location=Point([node.lat, node.lon], srid=4326),
                waypoint_type=point_type,
                gpx_file=self,
                tags=node.tags,
            )
            if "name" in node.tags:
                wp.name = node.tags.get("name")

            c = GPXTrackWayPoint.objects.all().filter(
                location__distance_lt=(Point([node.lat, node.lon], srid=4326), Distance(m=around_duplicate)),
                waypoint_type=point_type,
                gpx_file=self,
            )
            if c.count() == 0:
                sp = GPXTrackSegmentPoint.objects.filter(segment__in=self.get_all_segments_primary_keys()).annotate(
                    distance=FDistance('location', Point([node.lat, node.lon], srid=4326))
                ).order_by('-distance').last()
                wp.track_segment_point_nearby = sp
                wp.save()
                if wp.is_camping_site() or wp.is_hotel():
                    gpx_waypoint_find_route_from_track.delay(wp.pk)

        for way in result.get_ways():
            wp = GPXTrackWayPoint(
                location=Point([way.center_lat, way.center_lon], srid=4326),
                waypoint_type=point_type,
                gpx_file=self,
                tags=way.tags,
            )
            if "name" in way.tags:
                wp.name = way.tags.get("name")

            c = GPXTrackWayPoint.objects.all().filter(
                location__distance_lt=(Point([way.center_lat, way.center_lon], srid=4326), Distance(m=around_duplicate)),
                waypoint_type=point_type,
                gpx_file=self,
            )
            if c.count() == 0:
                sp = GPXTrackSegmentPoint.objects.filter(segment__in=self.get_all_segments_primary_keys()).annotate(
                    distance=FDistance('location', Point([way.center_lat, way.center_lon], srid=4326))
                ).order_by('-distance').last()
                wp.track_segment_point_nearby = sp
                wp.save()
                if wp.is_camping_site() or wp.is_hotel():
                    gpx_waypoint_find_route_from_track.delay(wp.pk)

    def load_file_to_database(self) -> None:
        gpxfile = GPX.from_file(self.file.path)

        if gpxfile.name is not None and gpxfile.name != '':
            self.name = gpxfile.name
            self.save()

        track_number = 1
        segment_number = 0
        for track in gpxfile.tracks:
            if track.name is not None and track.name != '':
                name = track.name
            else:
                name = "Track {}".format(track_number)
            track_number += 1

            gpx_track = GPXTrack(
                gpx_file=self,
                name=name,
                distance=track.distance,
            )
            gpx_track.save()

            for segment in track.trksegs:
                s = GPXTrackSegment(
                    number=segment_number,
                    track=gpx_track,
                    distance=segment.distance,
                )
                s.save()
                segment_number += 1
                segment_total_ascent = 0
                segment_total_descent = 0

                b_points = []
                point_number = 0
                priv_point = None
                for point in segment.trkpts:
                    elevation_diff_to_previous = None
                    if priv_point is not None:
                        if priv_point.elevation is not None and point.ele is not None:
                            elevation_diff_to_previous = priv_point.elevation - point.ele

                    p = GPXTrackSegmentPoint(
                        segment=s,
                        location=Point([point.lat, point.lon], srid=4326),
                        elevation=point.ele,
                        number=point_number,
                        elevation_diff_to_previous=elevation_diff_to_previous,
                    )
                    b_points.append(p)
                    priv_point = p
                    point_number += 1

                    if elevation_diff_to_previous is not None:
                        if elevation_diff_to_previous > 0:
                            segment_total_descent += elevation_diff_to_previous
                        else:
                            segment_total_ascent += elevation_diff_to_previous

                GPXTrackSegmentPoint.objects.bulk_create(b_points)
                del b_points

                s.total_ascent = abs(segment_total_ascent)
                s.total_descent = abs(segment_total_descent)
                s.save(update_fields=['total_ascent', 'total_descent'])


class GPXTrack(TimeStampedModel):
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=200, null=False, blank=False)
    distance = models.FloatField()

    def __str__(self) -> str:
        return f"GPX Track {self.name}"

    class Meta:
        ordering = ['name',]

    def get_human_distance(self) -> str:
        d = int(self.distance / 1000)
        return f"{d} km"

    def get_total_ascent(self) -> int:
        d = self.segments.all().aggregate(ascent=Sum('total_ascent'))

        if d.get('ascent', None):
            return int(d.get('ascent', None))

        return None

    def get_total_descent(self) -> int:
        d = self.segments.all().aggregate(descent=Sum('total_descent'))

        if d.get('descent', None):
            return int(d.get('descent', None))

        return None


class GPXTrackSegment(TimeStampedModel):
    number = models.IntegerField(null=False, blank=False, default=0)
    track = models.ForeignKey("GPXTrack", on_delete=models.CASCADE, related_name='segments')
    distance = models.FloatField()
    total_ascent = models.FloatField(null=True, blank=False)
    total_descent = models.FloatField(null=True, blank=False)

    def __str__(self) -> str:
        return f"GPX Track {self.track.name} Segment {self.number}"

    class Meta:
        ordering = ['track__name', 'number',]

    def get_human_distance(self) -> str:
        d = int(self.distance / 1000)
        return f"{d} km"


class GPXTrackSegmentPoint(TimeStampedModel):
    number = models.BigIntegerField(null=True, db_index=True)
    segment = models.ForeignKey("GPXTrackSegment", on_delete=models.CASCADE, related_name='points')
    location = models.PointField(db_index=True)
    elevation = models.FloatField(null=True, blank=False)
    elevation_diff_to_previous = models.FloatField(null=True, blank=False)

    def __str__(self) -> str:
        return f"{self.number}"

    class Meta:
        ordering = ['segment__pk', 'number',]

    def get_previous(self):
        if self.number == 0:
            # we are already on the start
            return None

        return GPXTrackSegmentPoint.objects.filter(segment=self.segment, number=(self.number + 1))

    def get_next(self):
        try:
            return GPXTrackSegmentPoint.objects.filter(segment=self.segment, number=(self.number + 1))
        except ObjectDoesNotExist:
            return None


class GPXFileUserSegmentSplit(TimeStampedModel):
    name = models.CharField(null=True, blank=False)
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='user_segments')
    point_start = models.ForeignKey("GPXTrackSegmentPoint", on_delete=models.CASCADE, related_name='user_splits_start')
    point_end = models.ForeignKey("GPXTrackSegmentPoint", on_delete=models.CASCADE, related_name='user_splits_end')

    distance = models.FloatField(null=True, blank=False)
    total_ascent = models.FloatField(null=True, blank=False)
    total_descent = models.FloatField(null=True, blank=False)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        ordering = ['point_start__pk', 'id',]

    def get_human_distance(self) -> str:
        if self.distance:
            d = int(self.distance / 1000)
        else:
            d = 0
        return f"{d} km"

    def get_total_ascent(self) -> int | None:
        if self.total_ascent:
            return int(self.total_ascent)

        return None

    def get_total_descent(self) -> int | None:
        if self.total_descent:
            return int(self.total_descent)

        return None

    @staticmethod
    def add_segment(gpx_file, start, end, name):
        if start.get('segment_pk', None) != end.get('segment_pk', None):
            raise Exception("segment_pk of end vs start !=")

        point_start = GPXTrackSegmentPoint.objects.filter(
            segment__id=start.get('segment_pk', None),
            segment__track__gpx_file=gpx_file,
            location=Point([start.get('lat', 0), start.get('lon', 0)], srid=4326),
        ).first()

        point_end = GPXTrackSegmentPoint.objects.filter(
            segment__id=end.get('segment_pk', None),
            segment__track__gpx_file=gpx_file,
            location=Point([end.get('lat', 0), end.get('lon', 0)], srid=4326),
        ).first()

        if point_start is None:
            return {'status': 'error', 'text': 'Start Point not found?!?'}

        if point_end is None:
            return {'status': 'error', 'text': 'End Point not found?!?'}

        if point_start.segment.pk != point_end.segment.pk:
            return {'status': 'error', 'text': 'Track is on two different GPX Segments'}

        if point_start.number > point_end.number:
            return {'status': 'error', 'text': 'Start Point is after the End Point'}

        points = GPXTrackSegmentPoint.objects.filter(
            segment__id=start.get('segment_pk', None),
            number__gte=point_start.number,
            number__lte=point_end.number,
        )
        segment_total_ascent = 0
        segment_total_descent = 0
        total_distance = 0
        priv_point = None

        for p in points:
            elevation_diff_to_previous = None

            if priv_point is not None:
                if priv_point.elevation is not None and p.elevation is not None:
                    elevation_diff_to_previous = priv_point.elevation - p.elevation

            if priv_point is not None:
                total_distance += geopy_distance.distance(
                    (priv_point.location.x, priv_point.location.y),
                    (p.location.x, p.location.y)
                ).m
            priv_point = p

            if elevation_diff_to_previous is not None:
                if elevation_diff_to_previous > 0:
                    segment_total_descent += elevation_diff_to_previous
                else:
                    segment_total_ascent += elevation_diff_to_previous

        segment = GPXFileUserSegmentSplit(
            gpx_file=gpx_file,
            name=name,
            point_start=point_start,
            point_end=point_end,
            total_ascent=abs(segment_total_ascent),
            total_descent=abs(segment_total_descent),
            distance=total_distance,
        )
        segment.save()

        return {'status': 'ok'}


class GPXWayPointType(models.Model):
    name = models.TextField(max_length=100, null=False, blank=False)
    gpx_sym_name = models.CharField(max_length=100)
    osm_name = models.TextField(max_length=100, null=False, blank=False)
    osm_value = models.TextField(max_length=100, null=False, blank=False)
    osm_query_type = models.CharField(max_length=10, null=False, blank=False, default='=')
    around = models.IntegerField(null=False, blank=False)
    around_max = models.IntegerField(null=False, blank=False)
    around_duplicate = models.IntegerField(null=False, blank=False, default=3000)
    marker_filename = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name

    def get_json_data(self) -> dict:
        data = {
            "name": self.name,
            "html_id": self.html_id(),
            "marker_image_path": self.marker_image_path(),
        }
        return data

    def html_id(self) -> str:
        return "{}_{}".format(self.osm_name, self.osm_value).replace('|', '')

    def marker_image_path(self) -> str:
        return '/static/{}'.format(self.marker_filename)


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
                "html_id": self.waypoint_type.html_id(),
                "marker_image_path": self.waypoint_type.marker_image_path(),

            }
        }
        if self.has_gpx_track_to():
            data["track_to_waypoint"] = {
                "length": self.track_to_waypoint.get_away_kilometer(),
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

    def get_url(self) -> str:
        return self.tags.get('website', None)

    def is_camping_site(self) -> bool:
        if self.waypoint_type.osm_value == 'camp_site':
            return True
        return False

    def is_hotel(self) -> bool:
        if 'hotel' in self.waypoint_type.osm_value:
            return True
        return False


class GPXTrackWayPointFromTrack(TimeStampedModel):
    waypoint = models.OneToOneField("GPXTrackWayPoint", on_delete=models.CASCADE, related_name='track_to_waypoint')
    geojson = models.JSONField(default=dict, null=False, blank=False)
    away_kilometer = models.FloatField(null=False, blank=False, default=0.0)

    def __str__(self) -> str:
        return f"{self.away_kilometer}"

    def get_away_kilometer(self) -> int:
        if self.away_kilometer > 1:
            return int(self.away_kilometer)
        else:
            return 1

    def get_geojson(self) -> dict:
        fc = geojson.FeatureCollection(features=[])
        fc.features.append(geojson.Feature(
            geometry=geojson.LineString(coordinates=self.geojson),
            properties={
                'color': '#448137',
                'weight': 3,
                'opacity': 0.7,
            }
        ))

        return fc

    def get_gpx_track(self) -> str:
        gpx = GPX()
        gpx.creator = 'GPX Tools by hggh'
        if self.waypoint.name != "":
            name = f"to {self.waypoint.name}"
        else:
            name = f"to {self.waypoint.waypoint_type.osm_value}"
        gpx.name = name

        track = Track()
        track.name = name

        segment = TrackSegment()

        for latlon in self.geojson:
            w = Waypoint()
            w.lat = latlon[1]
            w.lon = latlon[0]

            segment.points.append(w)

        track.trksegs = [segment]
        gpx.tracks = [track]

        return gpx.to_string()


@receiver(post_delete, sender=GPXFile)
def gpx_file_delete_file(sender, instance, *args, **kwargs) -> None:
    p = instance.file.path
    if os.path.exists(p):
        os.remove(p)

    geojson = os.path.join(settings.LOCAL_GEOJSON_TEMP_DIRECTORY, f"{instance.slug}.geojson")
    if os.path.exists(geojson):
        os.remove(geojson)
