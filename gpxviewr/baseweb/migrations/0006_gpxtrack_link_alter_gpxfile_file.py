# Generated by Django 5.1.6 on 2025-03-01 09:55

import django.core.files.storage
import pathlib
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseweb', '0005_gpxwaypointtype_checked'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxtrack',
            name='link',
            field=models.URLField(max_length=6000, null=True),
        ),
    ]
