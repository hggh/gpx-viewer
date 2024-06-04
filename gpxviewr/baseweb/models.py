from pathlib import Path
import secrets
import time
import os
import geojson
import json
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
from django.db.models.signals import post_delete, pre_delete
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

    def is_demo_track(self):
        return self.slug == settings.DEMO_TRACK_SLUG

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

    def get_user_segment_splits(self, segment_pk=None) -> list:
        data = []

        if segment_pk is not None:
            segments = self.user_segments.all().filter(point_start__segment__id=segment_pk)
        else:
            segments = self.user_segments.all()

        data = []

        for s in segments:
            segment = {
                "name": s.name,
                "id": s.pk,
                "segment_pk": s.point_start.segment.id,
                "start": {
                    "number": s.point_start.number,
                    "lat": float(s.point_start.location.x),
                    "lon": float(s.point_start.location.y),
                },
                "end": {
                    "number": s.point_end.number,
                    "lat": float(s.point_end.location.x),
                    "lon": float(s.point_end.location.y),
                }
            }
            data.append(segment)

        return data

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

                if len(points) > 0:
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

    def get_gpx_json_filename(self) -> str:
        return os.path.join(settings.LOCAL_GEOJSON_TEMP_DIRECTORY, f"gpx_file_info_{self.pk}.json")

    def get_json_data(self):
        if os.path.exists(self.get_gpx_json_filename()):
            return json.loads(Path(self.get_gpx_json_filename()).read_text())

        return None

    def load_file_to_database(self) -> None:
        json_data = []
        gpxfile = GPX.from_file(self.file.path)

        if gpxfile.name is not None and gpxfile.name != '':
            self.name = gpxfile.name
            self.save()

        track_number = 1
        for track in gpxfile.tracks:
            if track.name is not None and track.name != '':
                name = track.name
            else:
                name = "Track {}".format(track_number)
            track_number += 1

            track_has_segments_with_points = False
            if len(track.trksegs) > 0:
                for segment in track.trksegs:
                    if len(segment.trkpts) > 0:
                        track_has_segments_with_points = True
                        continue

            if track_has_segments_with_points is False:
                print("{} seems to have to points in any segment".format(
                    self.file.path,
                ))
                continue

            gpx_track = GPXTrack(
                gpx_file=self,
                name=name,
                distance=track.distance,
            )
            gpx_track.save()

            track_data = {
                'name': name,
                'slug': self.slug,
                'track_id': gpx_track.pk,
                'distance': track.distance,
                'segments': [],
            }

            segment_number = 0
            color_int = 0
            for segment in track.trksegs:
                if len(segment.trkpts) == 0:
                    print("{}: Segment {} has no points".format(self.file.path, segment_number))
                    continue

                s = GPXTrackSegment(
                    number=segment_number,
                    track=gpx_track,
                    distance=segment.distance,
                )
                s.save()
                segment_number += 1
                segment_total_ascent = 0
                segment_total_descent = 0

                segment_data = {
                    'number': s.number,
                    'segment_id': s.pk,
                    'distance': segment.distance,
                    'color': self.line_colors[color_int],
                    'points': [],
                }

                color_int += 1
                if color_int >= len(self.line_colors):
                    color_int = 0

                b_points = []
                point_number = 0
                priv_point = None
                total_distance = 0
                for point in segment.trkpts:
                    elevation_diff_to_previous = None
                    if priv_point is not None:
                        if priv_point.elevation is not None and point.ele is not None:
                            elevation_diff_to_previous = priv_point.elevation - point.ele

                        m = geopy_distance.distance((priv_point.location.x, priv_point.location.y), (point.lat, point.lon)).m
                    else:
                        m = 0
                    total_distance += m

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

                    if point.ele:
                        ele = float(point.ele)
                    else:
                        ele = 0

                    segment_data['points'].append({
                        'lat': float(point.lat),
                        'lon': float(point.lon),
                        'distance': total_distance,
                        'elevation': ele,
                        'point_number': p.number,
                    })

                    if elevation_diff_to_previous is not None:
                        if elevation_diff_to_previous > 0:
                            segment_total_descent += elevation_diff_to_previous
                        else:
                            segment_total_ascent += elevation_diff_to_previous

                GPXTrackSegmentPoint.objects.bulk_create(b_points)
                del b_points
                track_data['segments'].append(segment_data)

                s.total_ascent = abs(segment_total_ascent)
                s.total_descent = abs(segment_total_descent)
                s.save(update_fields=['total_ascent', 'total_descent'])

            json_data.append(track_data)

        Path(self.get_gpx_json_filename()).write_text(json.dumps(json_data))


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

        return GPXTrackSegmentPoint.objects.get(segment=self.segment, number=(self.number - 1))

    def get_next(self):
        try:
            return GPXTrackSegmentPoint.objects.get(segment=self.segment, number=(self.number + 1))
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

    def get_segment_id(self) -> int:
        return self.point_start.segment.pk

    def generate_gpx(self) -> str:
        points = GPXTrackSegmentPoint.objects.filter(
            segment__id=self.point_start.segment.pk,
            number__gte=self.point_start.number,
            number__lte=self.point_end.number,
        )

        gpx = GPX()
        gpx.creator = 'GPX Tools by hggh'
        gpx.name = self.name

        track = Track()
        track.name = self.name
        segment = TrackSegment()

        for point in points:
            w = Waypoint()
            w.lat = point.location.x
            w.lon = point.location.y
            w.ele = point.elevation

            segment.points.append(w)

        track.trksegs = [segment]
        gpx.tracks = [track]

        return gpx.to_string()

    @staticmethod
    def add_segment(gpx_file, segment_pk, point_number):
        point = GPXTrackSegmentPoint.objects.get(
            segment__id=segment_pk,
            segment__track__gpx_file=gpx_file,
            number=point_number,
        )
        update_splits = []

        # check if there are any splits?
        splits = GPXFileUserSegmentSplit.objects.filter(
            gpx_file=gpx_file,
            point_start__segment_id=segment_pk,

        )
        if len(splits) == 0:
            s = GPXFileUserSegmentSplit(
                gpx_file=gpx_file,
                point_start=point.segment.points.all().first(),
                point_end=point,
            )
            s.save()
            update_splits.append(s)
            s = GPXFileUserSegmentSplit(
                gpx_file=gpx_file,
                point_start=point,
                point_end=point.segment.points.all().last(),
            )
            s.save()
            update_splits.append(s)
        else:
            # we go back on the track and try to find a split start
            start = GPXFileUserSegmentSplit.objects.filter(
                    gpx_file=gpx_file,
                    point_start__segment_id=segment_pk,
                    point_start__number__lt=point.number,
            ).order_by('point_start__number').last()

            if start:
                end_point = start.point_end

                start.point_end = point
                start.save()
                update_splits.append(start)

                s = GPXFileUserSegmentSplit(
                    gpx_file=gpx_file,
                    point_start=point,
                    point_end=end_point,
                )
                s.save()
                update_splits.append(s)

        GPXFileUserSegmentSplit.update_segments(update_splits, gpx_file=gpx_file, segment_pk=segment_pk)

    @staticmethod
    def update_segments(update_splits, gpx_file, segment_pk):
        for split in update_splits:
            points = GPXTrackSegmentPoint.objects.filter(
                segment__id=split.point_start.segment.id,
                number__gte=split.point_start.number,
                number__lte=split.point_end.number,
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
            split.total_ascent=abs(segment_total_ascent)
            split.total_descent=abs(segment_total_descent)
            split.distance=total_distance
            split.save()

        # name all splits
        splits = GPXFileUserSegmentSplit.objects.filter(
            gpx_file=gpx_file,
            point_start__segment_id=segment_pk,

        ).order_by('point_start__number')
        split_number = 1
        for split in splits:
            split.name = f"Track {split_number}"
            split.save()

            split_number += 1

        return None


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
        if self.tags.get('contact:website', None):
            return self.tags.get('contact:website')

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

    if os.path.exists(instance.get_gpx_json_filename()):
        os.remove(instance.get_gpx_json_filename())


@receiver(pre_delete, sender=GPXFile)
def gpx_file_pre_delete(sender, instance, *args, **kwargs) -> None:
    for track in instance.tracks.all():
        for segment in track.segments.all():
            segment.delete()
