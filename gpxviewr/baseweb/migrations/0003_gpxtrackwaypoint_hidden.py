# Generated by Django 4.2.7 on 2023-11-28 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseweb', '0002_gpxwaypointtype_osm_query_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxtrackwaypoint',
            name='hidden',
            field=models.BooleanField(default=False),
        ),
    ]
