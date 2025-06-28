from django.contrib.gis.db import models


class GPXWayPointType(models.Model):
    name = models.TextField(max_length=100, null=False, blank=False)
    gpx_sym_name = models.CharField(max_length=100)
    gpx_type_name = models.CharField(max_length=100)
    osmand_icon = models.CharField(max_length=100)
    osm_name = models.TextField(max_length=100, null=False, blank=False)
    osm_value = models.TextField(max_length=100, null=False, blank=False)
    osm_query_type = models.CharField(max_length=10, null=False, blank=False, default='=')
    osm_extra_query = models.CharField(max_length=100, null=True, blank=True, default='')
    around = models.IntegerField(null=False, blank=False)
    around_max = models.IntegerField(null=False, blank=False)
    around_duplicate = models.IntegerField(null=False, blank=False, default=3000)
    marker_filename = models.CharField(max_length=100, null=True)
    checked = models.BooleanField(null=False, default=True, blank=False)
    generate_track_to_waypoint = models.BooleanField(null=False, default=False, blank=False)

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
