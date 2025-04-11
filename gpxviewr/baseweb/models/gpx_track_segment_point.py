from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist

from django_extensions.db.models import TimeStampedModel


class GPXTrackSegmentPoint(TimeStampedModel):
    number = models.BigIntegerField(null=True, db_index=True)
    segment = models.ForeignKey("GPXTrackSegment", on_delete=models.CASCADE, related_name='points')
    location = models.PointField(db_index=True)
    elevation = models.FloatField(null=True, blank=False)
    elevation_diff_to_previous = models.FloatField(null=True, blank=False)
    distance = models.IntegerField(null=True, blank=True)

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
