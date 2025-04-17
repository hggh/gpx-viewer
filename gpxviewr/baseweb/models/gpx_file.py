from pathlib import Path
import secrets
import time
import os
import json
from geopy import distance as geopy_distance
from datetime import timedelta

from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models.functions import Distance as FDistance
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel

import overpy

import pandas
from gpx import GPX, Waypoint
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
        '#2f2faf',
        '#ff0066',
        '#1f1fbf',
        '#3ef0fb',
        '#502968',
        '#448137',
    ]

    slug = models.SlugField(default=generate_slug_token, editable=False, max_length=50)
    name = models.CharField(max_length=200, null=False, blank=False)
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

    def is_demo_track(self) -> bool:
        return self.slug == settings.DEMO_TRACK_SLUG

    def get_job_status(self) -> str:
        return self.job_status_fields.get(self.job_status, 'unkown')

    def job_is_finished(self) -> bool:
        if self.get_job_status() == 'finished':
            return True
        return False

    def get_all_segments_primary_keys(self):
        from .gpx_track_segment import GPXTrackSegment

        return GPXTrackSegment.objects.all().filter(track__in=self.tracks.all().values_list('pk'))

    def get_waypoint_types(self) -> list:
        from .gpx_way_point_type import GPXWayPointType

        data = []
        for wtp in GPXWayPointType.objects.all():
            o = self.wpt_options.get(wtp.name, {})

            if o.get('enabled', False) is True:
                data.append(wtp)

        return data

    def get_waypoint_types_with_entries(self):
        from .gpx_way_point_type import GPXWayPointType

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
                    time.sleep(1.5)

    def query_data_osm(self, points, around_meters, point_type, around_duplicate) -> None:
        from baseweb.tasks import gpx_waypoint_find_route_from_track
        from baseweb.models import GPXTrackWayPoint, GPXTrackSegmentPoint

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
        try:
            result = api.query(overpass_query)
        except overpy.exception.OverpassTooManyRequests:
            print("OverpassTooManyRequests - retry it after sleep")
            time.sleep(5)
            return self.query_data_osm(points=points, around_meters=around_meters, point_type=point_type, around_duplicate=around_duplicate)
        except overpy.exception.OverpassGatewayTimeout:
            print("OverpassGatewayTimeout - retry")
            time.sleep(5)
            return self.query_data_osm(points=points, around_meters=around_meters, point_type=point_type, around_duplicate=around_duplicate)

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
                    caldistance=FDistance('location', Point([node.lat, node.lon], srid=4326))
                ).order_by('-caldistance').last()
                wp.track_segment_point_nearby = sp
                wp.save()
                if wp.waypoint_type.generate_track_to_waypoint is True:
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
                    caldistance=FDistance('location', Point([way.center_lat, way.center_lon], srid=4326))
                ).order_by('-caldistance').last()
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
        from baseweb.models import GPXTrackSegmentPoint, GPXTrack, GPXTrackSegment
        json_data = []
        gpxfile = GPX.from_file(self.file.path)

        if gpxfile.name is not None and gpxfile.name != '':
            self.name = gpxfile.name[:199] if len(gpxfile.name) > 199 else gpxfile.name
            self.save()

        track_number = 1
        for track in gpxfile.tracks:
            track_link = None
            if track.name is not None and track.name != '':
                name = track.name[:199] if len(track.name) > 199 else track.name
            else:
                name = "Track {}".format(track_number)
            track_number += 1

            for l in track.links:
                if l.href and len(l.href) <= 6000:
                    try:
                        URLValidator().__call__(l.href)
                        track_link = l.href
                        break
                    except ValidationError as e:
                        print(f"URL not valid: {gpxfile}: {l.href} with error: {e}")
                        pass

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
                link=track_link,
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
                        distance=total_distance,
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
