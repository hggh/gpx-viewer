import logging

from django.utils import timezone
from baseweb.models import (
    GPXFile,
    GPXTrack,
    GPXWayPointType,
)

from celery import shared_task


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
def gpx_file_load_into_database(gpx_file_pk):
    gpx_file = GPXFile.objects.get(pk=gpx_file_pk)
    gpx_file.job_status = 2
    gpx_file.save(update_fields=['job_status'])

    gpx_file.load_file_to_database()

    gpx_flile_query_osm.delay(gpx_file_pk)


@shared_task
def gpx_file_delete_after_days():
    logger = logging.getLogger(__name__)

    for gpx_file in GPXFile.objects.all().filter(delete_after__lte=timezone.now()):
        logger.warning(f"Delete Track {gpx_file.name}/{gpx_file.pk} delete date: {gpx_file.delete_after}")
        gpx_file.delete()
