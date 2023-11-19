from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList

from .models import GPXTrack, GPXWayPointType


def waypoint_types_choices():
    c = []
    for p in GPXWayPointType.objects.all():
        c.append((p.pk, p.pk))

    return c


class GPXTrackUploadForm(forms.ModelForm):
    wpt_options = forms.JSONField()
    file = forms.FileField()

    class Meta:
        model = GPXTrack
        fields = ["file", "wpt_options"]


class GPXTrackWayPointDownload(forms.Form):
    slug = forms.CharField()
    waypoint_types = forms.MultipleChoiceField(choices=waypoint_types_choices)
