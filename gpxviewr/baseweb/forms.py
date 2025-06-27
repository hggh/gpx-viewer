import os
from collections.abc import Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList

from .models import GPXFile, GPXWayPointType, generate_default_delete_after_date
from .valhalla import ValhallaRouting
from gcollection.models import GUser


def waypoint_types_choices():
    c = []
    for p in GPXWayPointType.objects.all():
        c.append((p.pk, p.pk))

    return c


class GPXFileUpdateForm(forms.ModelForm):
    name = forms.CharField(
        required=True,
        widget=forms.widgets.TextInput(attrs={'class': 'form-control'})
    )
    delete_after = forms.DateField(
        required=True,
        widget=forms.widgets.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
        )
    )
    perm_public_available = forms.BooleanField(
        initial=False,
        required=False,
        widget=forms.widgets.Select(
            attrs={'class': 'form-control'},
            choices=((True, 'Yes'), (False, 'No')),
        ),
    )
    class Meta:
        model = GPXFile
        fields = ['name', 'perm_public_available', 'delete_after',]


class GPXFileUploadForm(forms.ModelForm):
    wpt_options = forms.JSONField()
    file = forms.FileField()
    delete_after = forms.DateField(initial=generate_default_delete_after_date)
    bicycle_type = forms.ChoiceField(choices=ValhallaRouting.get_bicycle_types, widget=forms.Select(attrs={'class': 'form-select'}))
    user = forms.ModelChoiceField(
        queryset=GUser.objects.none(),
        required=False,
    )
    perm_public_available = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.widgets.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['user'].queryset = GUser.objects.all().filter(id=user.id)
        else:
            self.fields['user'].queryset = GUser.objects.none()

    class Meta:
        model = GPXFile
        fields = ["file", "wpt_options", "delete_after", "perm_public_available", "user"]
