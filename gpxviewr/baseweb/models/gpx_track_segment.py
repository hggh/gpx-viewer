from django.contrib.gis.db import models

from django_extensions.db.models import TimeStampedModel


class GPXTrackSegment(TimeStampedModel):
    number = models.IntegerField(null=False, blank=False, default=0)
    track = models.ForeignKey("GPXTrack", on_delete=models.CASCADE, related_name='segments')
    distance = models.FloatField()
    total_ascent = models.FloatField(null=True, blank=False)
    total_descent = models.FloatField(null=True, blank=False)

    def __str__(self) -> str:
        return f"GPX Track {self.track.name} Segment {self.number}"

    class Meta:
        ordering = ['track__name', 'number',]

    def get_human_distance(self) -> str:
        d = int(self.distance / 1000)
        return f"{d} km"
