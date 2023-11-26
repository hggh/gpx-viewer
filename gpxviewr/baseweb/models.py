from pathlib import Path
import secrets
import time
import os
from datetime import timedelta

from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.measure import Distance
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.db.models.signals import post_delete
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel

import overpy

import numpy
import pandas
from gpx import GPX, Waypoint
from gpx.waypoint import Link


fs = FileSystemStorage(location=settings.LOCAL_STORAGE_DIRECTORY)


def generate_slug_token():
    return secrets.token_urlsafe(30)


def generate_default_delete_after_date():
    return (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d')


class GPXTrack(TimeStampedModel):
    slug = models.SlugField(default=generate_slug_token, editable=False, max_length=50)
    name = models.TextField(max_length=100, null=False, blank=False)
    tracks = models.IntegerField(default=1, null=False)
    wpt_options = models.JSONField(default=dict)
    job_status = models.BooleanField(default=False, null=False)
    delete_after = models.DateField(null=False, blank=False)

    file = models.FileField(storage=fs, upload_to="gpx_track/%Y/%m/%d/")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("gpx-track-detail", kwargs={"slug": self.slug})

    def save(self, **kwargs):
        if self.name is None or self.name == '':
            self.name = self.file.name.replace('.gpx', '')

        return super().save(**kwargs)

    def is_multi_track(self):
        if self.tracks > 1:
            return True
        return False

    def get_waypoint_types_with_entries(self):
        wtps = []
        for wtp in GPXWayPointType.objects.all():
            wtps.append({
                'object': wtp,
                'waypoints': self.waypoints.all().filter(waypoint_type=wtp),
            })
        return wtps

    def generate_download_gpx_file(self, options):
        gpx = GPX()
        gpx.creator = 'GPX Tools by hggh'
        waypoints = []

        for w in self.waypoints.all().filter(waypoint_type__in=options):
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

    def leaflet_polyline(self):
        gpxfile = GPX.from_file(self.file.path)
        points = []

        for track in gpxfile.tracks:
            for segment in track.trksegs:
                for point in segment.trkpts:
                    points.append([float(point.lat), float(point.lon)])

        return points

    def generate_waypoints(self, point_type, around_meters=None, around_duplicate=0):
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

    def query_data_osm(self, points, around_meters, point_type, around_duplicate):
        track_points = pandas.DataFrame(points, columns=["lat", "lon"])
        track_latlong_flatten = ",".join(track_points.to_numpy().flatten().astype("str"))

        api = overpy.Overpass()
        overpass_query = f"""
            [out:json][timeout: 500];
            (
                nwr["{point_type.osm_name}" = "{point_type.osm_value}"](around:{around_meters},{track_latlong_flatten});
            );
            out center;
        """
        result = api.query(overpass_query)

        for node in result.get_nodes():
            wp = GPXTrackWayPoint(
                location=Point([node.lat, node.lon]),
                waypoint_type=point_type,
                gpx_track=self,
                tags=node.tags,
            )
            if "name" in node.tags:
                wp.name = node.tags.get("name")

            c = GPXTrackWayPoint.objects.all().filter(
                location__distance_lt=(Point([node.lat, node.lon]), Distance(m=around_duplicate)),
                waypoint_type=point_type,
                gpx_track=self,
            )
            if c.count() == 0:
                wp.save()

        for way in result.get_ways():
            wp = GPXTrackWayPoint(
                location=Point([way.center_lat, way.center_lon]),
                waypoint_type=point_type,
                gpx_track=self,
                tags=way.tags,
            )
            if "name" in way.tags:
                wp.name = way.tags.get("name")

            c = GPXTrackWayPoint.objects.all().filter(
                location__distance_lt=(Point([way.center_lat, way.center_lon]), Distance(m=around_duplicate)),
                waypoint_type=point_type,
                gpx_track=self,
            )
            if c.count() == 0:
                wp.save()


class GPXWayPointType(models.Model):
    name = models.TextField(max_length=100, null=False, blank=False)
    gpx_sym_name = models.CharField(max_length=100)
    osm_name = models.TextField(max_length=100, null=False, blank=False)
    osm_value = models.TextField(max_length=100, null=False, blank=False)
    around = models.IntegerField(null=False, blank=False)
    around_max = models.IntegerField(null=False, blank=False)
    around_duplicate = models.IntegerField(null=False, blank=False, default=3000)
    marker_filename = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name

    def get_json_data(self):
        data = {
            "name": self.name,
            "html_id": self.html_id(),
            "marker_image_path": self.marker_image_path(),
        }
        return data

    def html_id(self):
        return "{}_{}".format(self.osm_name, self.osm_value)

    def marker_image_path(self):
        return '/static/{}'.format(self.marker_filename)


class GPXTrackWayPoint(TimeStampedModel):
    gpx_track = models.ForeignKey("GPXTrack", on_delete=models.CASCADE, related_name='waypoints')
    waypoint_type = models.ForeignKey("GPXWayPointType", on_delete=models.CASCADE, related_name='waypoints')
    name = models.CharField(max_length=100, null=False, blank=True)
    tags = models.JSONField(default=dict)

    location = models.PointField(geography=True, default=Point(0.0, 0.0), db_index=True)

    def get_json_data(self):
        data = {
            "lat": self.location.x,
            "lon": self.location.y,
            "class_name": self.get_marker_css_name(),
            "url": self.get_url(),
            "name": self.name,
            "waypoint_type": {
                "html_id": self.waypoint_type.html_id(),
                "marker_image_path": self.waypoint_type.marker_image_path(),

            }
        }
        return data

    def get_marker_css_name(self):
        if self.is_camping_site() is True and self.get_url():
            return 'marker_camping_with_url'
        return 'marker_default'

    def get_url(self):
        return self.tags.get('website', None)

    def is_camping_site(self):
        if self.waypoint_type.osm_value == 'camp_site':
            return True
        return False


@receiver(post_delete, sender=GPXTrack)
def gpx_track_delete_file(sender, instance, *args, **kwargs):
    p = instance.file.path
    if os.path.exists(p):
        os.remove(p)
