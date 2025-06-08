from django.contrib.gis.db import models

from django_extensions.db.models import TimeStampedModel


class GCollectionWayPointType(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    image_name = models.CharField(max_length=30, null=False, blank=False)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name

    def get_icon_url(self) -> str:
        return f"/static/gcollection/{self.image_name}.svg"
