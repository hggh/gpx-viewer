import logging

from django.utils import timezone

from celery import shared_task

from baseweb.models import (
    GPXFile,
    GPXWayPointType,
    GPXTrackWayPoint,
    GPXTrackWayPointFromTrack,
    GPXTrackSegmentPoint,
)
from .valhalla import ValhallaRouting


@shared_task()
def gpx_flile_query_osm(gpx_file_pk):
    gpx_file = GPXFile.objects.get(pk=gpx_file_pk)
    gpx_file.job_status = 3
    gpx_file.save(update_fields=['job_status'])

    print("gpx_flile_query_osm: {}".format(gpx_file.name))

    try:
        for wpt in GPXWayPointType.objects.all():
            options = gpx_file.wpt_options.get(wpt.name, {})

            if options.get('enabled', False):
                print("WPT Name: {}".format(wpt.name))

                around = int(options.get('around', wpt.around))
                around_duplicate = int(options.get('around_duplicate', 0))

                if around > wpt.around_max:
                    print("{}: {}: around was to high ({})".format(
                        gpx_file.name,
                        wpt.name,
                        around,
                    ))
                    around = wpt.around_max

                gpx_file.generate_waypoints(point_type=wpt, around_meters=around, around_duplicate=around_duplicate)

        gpx_file.job_status = 4
        gpx_file.save()

    except Exception as e:
        print(f"Error on GPXFile PK {gpx_file.pk} with error: ")
        print(e)
        gpx_file.job_status = 5
        gpx_file.save()


@shared_task
def gpx_waypoint_find_route_from_track(waypoint_pk):
    waypoint = GPXTrackWayPoint.objects.get(pk=waypoint_pk)

    track_point = waypoint.track_segment_point_nearby

    targets = []

    track_points_q = GPXTrackSegmentPoint.objects.filter(
        segment=track_point.segment,
        number__gte=(track_point.number - 100),
        number__lte=(track_point.number + 100),
    )
    for point in track_points_q:
        targets.append({
            'lat': float(point.location.x),
            'lon': float(point.location.y)
        })

    r = ValhallaRouting(
        s_lat=float(waypoint.location.x),
        s_lon=float(waypoint.location.y),
    )
    point = r.query_shortest_point_by_street(targets=targets)

    if 'lat' not in point:
        print(f"Waypoint {waypoint_pk} with {targets} did not find a path?")

    r = ValhallaRouting(
        s_lat=point.get('lat', float(track_point.location.x)),
        s_lon=point.get('lon', float(track_point.location.y)),
    )

    data = r.query(
        d_lat=float(waypoint.location.x),
        d_lon=float(waypoint.location.y),
    )

    if 'length' in data and 'geojson' in data:
        t = GPXTrackWayPointFromTrack(
            waypoint=waypoint,
            geojson=data.get('geojson'),
            away_kilometer=data.get('length'),
        )
        t.save()


@shared_task
def pregenerate_d3js_data(gpx_file_pk) -> None:
    gpx_file = GPXFile.objects.get(pk=gpx_file_pk)

    for track in gpx_file.tracks.all():
        for segment in track.segments.all():
            segment.get_d3js()


@shared_task
def gpx_file_load_into_database(gpx_file_pk):
    gpx_file = GPXFile.objects.get(pk=gpx_file_pk)
    gpx_file.job_status = 2
    gpx_file.save(update_fields=['job_status'])

    gpx_file.load_file_to_database()

    pregenerate_d3js_data.delay(gpx_file_pk)
    gpx_flile_query_osm.delay(gpx_file_pk)


@shared_task
def gpx_file_delete_after_days():
    logger = logging.getLogger(__name__)

    for gpx_file in GPXFile.objects.all().filter(delete_after__lte=timezone.now()):
        logger.warning(f"Delete Track {gpx_file.name}/{gpx_file.pk} delete date: {gpx_file.delete_after}")
        gpx_file.delete()
