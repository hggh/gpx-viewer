# Generated by Django 5.0.1 on 2024-01-04 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseweb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gpxtracksegmentpoint',
            name='elevation_diff_to_previous',
            field=models.FloatField(null=True),
        ),
    ]
