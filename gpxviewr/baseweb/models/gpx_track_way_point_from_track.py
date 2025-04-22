import geojson

from django.contrib.gis.db import models

from django_extensions.db.models import TimeStampedModel
import gpxpy
import gpxpy.gpx


class GPXTrackWayPointFromTrack(TimeStampedModel):
    waypoint = models.OneToOneField("GPXTrackWayPoint", on_delete=models.CASCADE, related_name='track_to_waypoint')
    geojson = models.JSONField(default=dict, null=False, blank=False)
    away_kilometer = models.FloatField(null=False, blank=False, default=0.0)

    def __str__(self) -> str:
        return f"{self.away_kilometer}"

    def get_download_url(self) -> str:
        return f"/gpxtrack/{self.waypoint.gpx_file.slug}/download_gpx_track_to_waypoint/{self.waypoint.pk}"

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
        gpx = gpxpy.gpx.GPX()
        gpx.creator = 'GPXViewr by hggh'
        if self.waypoint.name != "":
            name = f"to {self.waypoint.name}"
        else:
            name = f"to {self.waypoint.waypoint_type.osm_value}"
        gpx.name = name

        track = gpxpy.gpx.GPXTrack()
        track.name = name

        segment = gpxpy.gpx.GPXTrackSegment()

        for latlon in self.geojson:
            w = gpxpy.gpx.GPXTrackPoint()
            w.latitude = latlon[1]
            w.longitude = latlon[0]

            segment.points.append(w)

        track.segments.append(segment)
        gpx.tracks.append(track)

        return gpx.to_xml()
