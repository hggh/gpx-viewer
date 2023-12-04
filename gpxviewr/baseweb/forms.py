import os
from collections.abc import Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList

from .models import GPXFile, GPXWayPointType, generate_default_delete_after_date


def waypoint_types_choices():
    c = []
    for p in GPXWayPointType.objects.all():
        c.append((p.pk, p.pk))

    return c


class GPXFileUploadForm(forms.ModelForm):
    wpt_options = forms.JSONField()
    file = forms.FileField()
    delete_after = forms.DateField(initial=generate_default_delete_after_date)

    class Meta:
        model = GPXFile
        fields = ["file", "wpt_options", "delete_after"]


class GPXTrackWayPointDownload(forms.Form):
    slug = forms.CharField()
    waypoint_types = forms.MultipleChoiceField(choices=waypoint_types_choices)
