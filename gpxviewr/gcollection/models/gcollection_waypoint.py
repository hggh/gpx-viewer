import re

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel


class GCollectionWayPoint(TimeStampedModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    gcollection = models.ForeignKey("gcollection.GCollection", on_delete=models.CASCADE, related_name='waypoints')
    waypoint_type = models.ForeignKey("gcollection.GCollectionWayPointType", on_delete=models.RESTRICT, related_name='waypoints')

    location = gis_models.PointField(default=Point(0.0, 0.0))

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def clean(self):
        if re.search(pattern=r'^[\w\s\./\-#~]+$', string=self.name) is None:
            raise ValidationError("name is not valid.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_location_leaflet(self):
        return {'lat': self.location.x, 'lng': self.location.y}
