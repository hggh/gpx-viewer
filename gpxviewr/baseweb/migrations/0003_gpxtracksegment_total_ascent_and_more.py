# Generated by Django 5.0.1 on 2024-01-06 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseweb', '0002_gpxtracksegmentpoint_elevation_diff_to_previous'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxtracksegment',
            name='total_ascent',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='gpxtracksegment',
            name='total_descent',
            field=models.FloatField(null=True),
        ),
    ]
