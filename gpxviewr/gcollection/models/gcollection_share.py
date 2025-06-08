from pathlib import Path
import secrets
import time
import os
import json
from geopy import distance as geopy_distance
from datetime import timedelta

from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.measure import Distance
from django.contrib.gis.db.models.functions import Distance as FDistance
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from django_extensions.db.models import TimeStampedModel


def generate_slug_token():
    return secrets.token_urlsafe(30)


def generate_default_valid_until():
    return (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d')


class GcollectionShare(TimeStampedModel):
    slug = models.SlugField(default=generate_slug_token, editable=False, max_length=50, unique=True)
    gcollection = models.ForeignKey("gcollection.GCollection", on_delete=models.CASCADE, related_name='shares')
    valid_until_date = models.DateField(null=False, blank=False)

    class Meta:
        pass
