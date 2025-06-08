import json
import re
from geopy import distance as geopy_distance
import pathlib

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django_extensions.db.models import TimeStampedModel

import gpxpy
import gpxpy.gpx

fs = FileSystemStorage(location=settings.LOCAL_STORAGE_DIRECTORY)

STATUS_CHOICES = (
    (1, 'uploaded'),
    (10, 'processed'),
    (99, 'error'),
)


class GCollectionGPXFile(TimeStampedModel):
    name = models.CharField(max_length=100, null=False, blank=False, db_index=True)
    date = models.DateField(null=False, blank=False, db_index=True)
    gcollection = models.ForeignKey("gcollection.GCollection", on_delete=models.CASCADE, related_name='gpx_files')

    job_status = models.IntegerField(default=1, null=False, choices=STATUS_CHOICES)
    file = models.FileField(storage=fs, upload_to="gcollection_gpx_file/%Y/%m/%d/", null=False, blank=False)

    distance = models.FloatField(null=True, blank=True)
    ascent = models.FloatField(null=True, blank=True)
    descent = models.FloatField(null=True, blank=True)
    bounds = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'name',]
        constraints = [
            models.UniqueConstraint(models.functions.Lower("name"), "gcollection", name='file_gcollection_name_unique'),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self):
        if re.search(pattern=r'^[\w\s\./\-#~]+$', string=self.name) is None:
            raise ValidationError("name is not valid.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_human_distance(self) -> str:
        if self.distance:
            d = int(self.distance / 1000)
            return f"{d} km"
        return ""

    def json(self):
        if self.get_json_filename().exists():
            return json.loads(self.get_json_filename().read_text())
        return []

    def get_json_filename(self) -> str:
        return pathlib.Path(settings.LOCAL_GEOJSON_TEMP_DIRECTORY, f"gcollection_{self.gcollection.pk}_{self.pk}.json")

    def generate_json(self) -> None:
        json_data = []

        f = open(self.file.path, 'r')
        gpxfile = gpxpy.parse(f)
        total_distance = 0
        total_ascent = 0
        total_descent = 0
        bounds = gpxfile.get_bounds()

        for track in gpxfile.tracks:
            track_has_segments_with_points = False
            if len(track.segments) > 0:
                for segment in track.segments:
                    if len(segment.points) > 0:
                        track_has_segments_with_points = True

            if track_has_segments_with_points is False:
                print("{} seems to have to points in any segment".format(
                    self.file.path,
                ))
                continue

            track_data = {
                'distance': track.length_3d(),
                'segments': [],
            }

            segment_distance = 0
            for segment in track.segments:
                if len(segment.points) == 0:
                    print("{}: Segment {} has no points".format(self.file.path))
                    continue

                segment_data = {
                    'distance': segment.length_3d(),
                    'points': [],
                }

                priv_point = None
                for point in segment.points:
                    elevation_diff_to_previous = None
                    if priv_point is not None:
                        if priv_point.elevation is not None and point.elevation is not None:
                            elevation_diff_to_previous = priv_point.elevation - point.elevation

                        m = geopy_distance.distance((priv_point.latitude, priv_point.longitude), (point.latitude, point.longitude)).m
                    else:
                        m = 0
                    total_distance += m
                    segment_distance += m

                    priv_point = point

                    if point.elevation:
                        ele = float(point.elevation)
                    else:
                        ele = 0

                    segment_data['points'].append({
                        'lat': float(point.latitude),
                        'lon': float(point.longitude),
                        'distance': segment_distance,
                        'elevation': ele,
                    })

                    if elevation_diff_to_previous is not None:
                        if elevation_diff_to_previous > 0:
                            total_descent += elevation_diff_to_previous
                        else:
                            total_ascent += elevation_diff_to_previous

                track_data['segments'].append(segment_data)

            json_data.append(track_data)

        self.ascent = abs(total_ascent)
        self.descent = abs(total_descent)
        self.distance = total_distance
        self.bounds = {
            'min_latitude': bounds.min_latitude,
            'min_longitude': bounds.min_longitude,
            'max_latitude': bounds.max_latitude,
            'max_longitude': bounds.max_longitude,
        }
        self.save(update_fields=['ascent', 'descent', 'distance', 'bounds'])

        pathlib.Path(self.get_json_filename()).write_text(json.dumps(json_data))


@receiver(post_delete, sender=GCollectionGPXFile)
def gpx_file_delete_file(sender, instance, *args, **kwargs) -> None:
    if instance.file:
        p = instance.file.path
        pathlib.Path(p).unlink(missing_ok=True)

    pathlib.Path(instance.get_json_filename()).unlink(missing_ok=True)
