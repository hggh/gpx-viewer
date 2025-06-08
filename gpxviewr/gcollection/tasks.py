import traceback
import smopy
import gpxpy
import pathlib
from PIL import ImageDraw, ImageColor

from celery import shared_task

from gcollection.models import GCollectionGPXFile, GCollection


@shared_task
def gc_gpx_file_process(gc_gpx_file_pk):
    gpx_file = GCollectionGPXFile.objects.get(pk=gc_gpx_file_pk)
    try:
        gpx_file.generate_json()

        gpx_file.save(update_fields=['job_status'])
    except Exception as e:
        print(traceback.print_exception(e))
        gpx_file.job_status = 99
        gpx_file.save(update_fields=['job_status'])
    else:
        gpx_file.gcollection.calculate_bounds()

        gpx_file.job_status = 10
        gpx_file.save(update_fields=['job_status'])

    gc_collection_og_image_generate(gpx_file.gcollection.id)


@shared_task
def gc_collection_og_image_generate(gc_collection_pk):
    g = GCollection.objects.get(pk=gc_collection_pk)
    b = g.bounds

    if b and b.get('min_latitude', None):
        map = smopy.Map((b.get('min_latitude'), b.get('min_longitude'), b.get('max_latitude'), b.get('max_longitude')), z=8)
        d = ImageDraw.Draw(map.img)

        for gpx_file in g.gpx_files.all():
            f = open(gpx_file.file.path, 'r')
            gpxfile = gpxpy.parse(f)
            for track in gpxfile.tracks:
                for segment in track.segments:
                    i = 0
                    for point in segment.points:
                        if i == 0 or i % 20 == 0:
                            x, y = map.to_pixels(float(point.latitude), float(point.longitude))

                            d.circle((x, y), radius=1, width=0, fill=ImageColor.getrgb("#ff0000"))

        map.img.save(pathlib.Path(g.get_og_image_filepath()), format='JPEG')
