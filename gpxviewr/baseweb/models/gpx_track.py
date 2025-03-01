from django.contrib.gis.db import models

from django_extensions.db.models import TimeStampedModel


class GPXTrack(TimeStampedModel):
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='tracks')
    name = models.CharField(max_length=200, null=False, blank=False)
    distance = models.FloatField()
    link = models.URLField(max_length=6000, null=True)

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
