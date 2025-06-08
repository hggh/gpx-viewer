import gpxpy
import re
import pathlib

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.urls import reverse

from django_extensions.db.models import TimeStampedModel


class GCollection(TimeStampedModel):
    user = models.ForeignKey("gcollection.GUser", on_delete=models.CASCADE, related_name='gcollections', null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    bounds = models.JSONField(null=True, blank=True)
    date = models.DateField(null=False, blank=False)

    class Meta:
        ordering = ['date', 'name',]
        constraints = [
            models.UniqueConstraint(models.functions.Lower("name"), "user", name='user_name_unique'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if re.search(pattern=r'^[\w\s\./\-#~]+$', string=self.name) is None:
            raise ValidationError("name is not valid.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('gcollection_detail', kwargs={"pk": self.pk})

    def get_og_image_filepath(self) -> str:
        return pathlib.Path(settings.LOCAL_GEOJSON_TEMP_DIRECTORY, f"gcollection_{self.pk}_og_image.jpeg")

    def has_og_image(self) -> bool:
        return pathlib.Path(self.get_og_image_filepath()).exists()

    def get_human_distance(self):
        distance = 0
        for i in self.gpx_files.all().exclude(distance=None).values_list('distance', flat=True):
            distance += i

        return str(int(distance / 1000)) + " km"

    def _min(self, v1, v2):
        if v1 is None:
            return v2

        return min(v1, v2)

    def _max(self, v1, v2):
        if v1 is None:
            return v2

        return max(v1, v2)

    def calculate_bounds(self):
        self.bounds = {}

        for gpx_file in self.gpx_files.all():
            if gpx_file.bounds is None:
                gpx_file.bounds = {}

            self.bounds = {
                'min_latitude': self._min(self.bounds.get('min_latitude', None), gpx_file.bounds.get('min_latitude', None)),
                'max_latitude': self._max(self.bounds.get('max_latitude', None), gpx_file.bounds.get('max_latitude', None)),
                'min_longitude': self._min(self.bounds.get('min_longitude', None), gpx_file.bounds.get('min_longitude', None)),
                'max_longitude': self._max(self.bounds.get('max_longitude', None), gpx_file.bounds.get('max_longitude', None)),
            }
        self.save(update_fields=['bounds'])

    def get_leaflet_bounds(self):
        if self.bounds:
            return [[self.bounds.get('min_latitude', 0), self.bounds.get('min_longitude', 0)], [self.bounds.get('max_latitude', 0), self.bounds.get('max_longitude', 0)]]
        return None


@receiver(post_delete, sender=GCollection)
def gpx_file_delete_file(sender, instance, *args, **kwargs) -> None:
    pathlib.Path(instance.get_og_image_filepath()).unlink(missing_ok=True)
