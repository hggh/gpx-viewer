from geopy import distance as geopy_distance


from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel

from gpx import GPX, Waypoint, Track
from gpx.track_segment import TrackSegment


class GPXFileUserSegmentSplit(TimeStampedModel):
    name = models.CharField(null=True, blank=False)
    gpx_file = models.ForeignKey("GPXFile", on_delete=models.CASCADE, related_name='user_segments')
    point_start = models.ForeignKey("GPXTrackSegmentPoint", on_delete=models.CASCADE, related_name='user_splits_start')
    point_end = models.ForeignKey("GPXTrackSegmentPoint", on_delete=models.CASCADE, related_name='user_splits_end')

    distance = models.FloatField(null=True, blank=False)
    total_ascent = models.FloatField(null=True, blank=False)
    total_descent = models.FloatField(null=True, blank=False)

    def __str__(self) -> str:
        return f"{self.name}"

    class Meta:
        ordering = ['point_start__pk', 'id',]

    def get_human_distance(self) -> str:
        if self.distance:
            d = int(self.distance / 1000)
        else:
            d = 0
        return f"{d} km"

    def get_total_ascent(self) -> int | None:
        if self.total_ascent:
            return int(self.total_ascent)

        return None

    def get_total_descent(self) -> int | None:
        if self.total_descent:
            return int(self.total_descent)

        return None

    def get_segment_id(self) -> int:
        return self.point_start.segment.pk

    def generate_gpx(self) -> str:
        from baseweb.models import GPXTrackSegmentPoint

        points = GPXTrackSegmentPoint.objects.filter(
            segment__id=self.point_start.segment.pk,
            number__gte=self.point_start.number,
            number__lte=self.point_end.number,
        )

        gpx = GPX()
        gpx.creator = 'GPX Tools by hggh'
        gpx.name = self.name

        track = Track()
        track.name = self.name
        segment = TrackSegment()

        for point in points:
            w = Waypoint()
            w.lat = point.location.x
            w.lon = point.location.y
            w.ele = point.elevation

            segment.points.append(w)

        track.trksegs = [segment]
        gpx.tracks = [track]

        return gpx.to_string()

    @staticmethod
    def add_segment(gpx_file, segment_pk, point_number):
        from baseweb.models import GPXTrackSegmentPoint

        point = GPXTrackSegmentPoint.objects.get(
            segment__id=segment_pk,
            segment__track__gpx_file=gpx_file,
            number=point_number,
        )
        update_splits = []

        # check if there are any splits?
        splits = GPXFileUserSegmentSplit.objects.filter(
            gpx_file=gpx_file,
            point_start__segment_id=segment_pk,

        )
        if len(splits) == 0:
            s = GPXFileUserSegmentSplit(
                gpx_file=gpx_file,
                point_start=point.segment.points.all().first(),
                point_end=point,
            )
            s.save()
            update_splits.append(s)
            s = GPXFileUserSegmentSplit(
                gpx_file=gpx_file,
                point_start=point,
                point_end=point.segment.points.all().last(),
            )
            s.save()
            update_splits.append(s)
        else:
            # we go back on the track and try to find a split start
            start = GPXFileUserSegmentSplit.objects.filter(
                    gpx_file=gpx_file,
                    point_start__segment_id=segment_pk,
                    point_start__number__lt=point.number,
            ).order_by('point_start__number').last()

            if start:
                end_point = start.point_end

                start.point_end = point
                start.save()
                update_splits.append(start)

                s = GPXFileUserSegmentSplit(
                    gpx_file=gpx_file,
                    point_start=point,
                    point_end=end_point,
                )
                s.save()
                update_splits.append(s)

        GPXFileUserSegmentSplit.update_segments(update_splits, gpx_file=gpx_file, segment_pk=segment_pk)

    @staticmethod
    def update_segments(update_splits, gpx_file, segment_pk):
        from baseweb.models import GPXTrackSegmentPoint

        for split in update_splits:
            points = GPXTrackSegmentPoint.objects.filter(
                segment__id=split.point_start.segment.id,
                number__gte=split.point_start.number,
                number__lte=split.point_end.number,
            )
            segment_total_ascent = 0
            segment_total_descent = 0
            total_distance = 0
            priv_point = None

            for p in points:
                elevation_diff_to_previous = None

                if priv_point is not None:
                    if priv_point.elevation is not None and p.elevation is not None:
                        elevation_diff_to_previous = priv_point.elevation - p.elevation

                if priv_point is not None:
                    total_distance += geopy_distance.distance(
                        (priv_point.location.x, priv_point.location.y),
                        (p.location.x, p.location.y)
                    ).m
                priv_point = p

                if elevation_diff_to_previous is not None:
                    if elevation_diff_to_previous > 0:
                        segment_total_descent += elevation_diff_to_previous
                    else:
                        segment_total_ascent += elevation_diff_to_previous
            split.total_ascent=abs(segment_total_ascent)
            split.total_descent=abs(segment_total_descent)
            split.distance=total_distance
            split.save()

        # name all splits
        splits = GPXFileUserSegmentSplit.objects.filter(
            gpx_file=gpx_file,
            point_start__segment_id=segment_pk,

        ).order_by('point_start__number')
        split_number = 1
        for split in splits:
            split.name = f"Track {split_number}"
            split.save()

            split_number += 1

        return None
