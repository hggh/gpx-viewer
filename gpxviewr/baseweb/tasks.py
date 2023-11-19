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

            if around > wpt.around_max:
                print("{}: {}: around was to high ({})".format(
                    g.name,
                    wpt.name,
                    around,
                ))
                around = wpt.around_max

            g.generate_waypoints(point_type=wpt, around_meters=around)

    g.job_status = True
    g.save()
