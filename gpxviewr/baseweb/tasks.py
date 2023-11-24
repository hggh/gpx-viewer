import logging

from django.utils import timezone
from baseweb.models import (
    GPXTrack,
    GPXWayPointType,
)

from celery import shared_task


@shared_task()
def gpx_track_query_osm(gpx_track_pk):
    g = GPXTrack.objects.get(pk=gpx_track_pk)

    print("gpx_track_query_osm: {}".format(g.name))

    for wpt in GPXWayPointType.objects.all():
        options = g.wpt_options.get(wpt.name, {})

        if options.get('enabled', False):
            print("WPT Name: {}".format(wpt.name))

            around = int(options.get('around', wpt.around))
            around_duplicate = int(options.get('around_duplicate', 0))

            if around > wpt.around_max:
                print("{}: {}: around was to high ({})".format(
                    g.name,
                    wpt.name,
                    around,
                ))
                around = wpt.around_max

            g.generate_waypoints(point_type=wpt, around_meters=around, around_duplicate=around_duplicate)

    g.job_status = True
    g.save()


@shared_task
def gpx_track_delete_after_days():
    logger = logging.getLogger(__name__)

    for gpx_track in GPXTrack.objects.all().filter(delete_after__lte=timezone.now()):
        logger.warning(f"Delete Track {gpx_track.name}/{gpx_track.pk} delete date: {gpx_track.delete_after}")
        gpx_track.delete()
        # FIXME: auch das File löschen!
