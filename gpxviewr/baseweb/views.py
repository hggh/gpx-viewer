from typing import Any
from django import http
from django.shortcuts import redirect
from django.contrib import messages
from django.db import models
from django.forms.forms import BaseForm
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, CreateView, DetailView, FormView, UpdateView
from django.http import HttpResponse, JsonResponse, Http404

from django.conf import settings

from .models import (
    GPXFile,
    GPXTrack,
    GPXWayPointType,
    GPXTrackWayPoint,
    GPXFileUserSegmentSplit,
    generate_default_delete_after_date,
)

from .forms import (
    GPXTrackWayPointDownload,
    GPXFileUploadForm,
)

from .tasks import gpx_file_load_into_database


class RobotsTxtView(TemplateView):
    template_name = 'robots.txt'


class IndexView(CreateView):
    template_name = 'index.html'
    model = GPXFile
    form_class = GPXFileUploadForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['waypoint_types'] = GPXWayPointType.objects.all()

        try:
            context['demo_track'] = GPXFile.objects.get(slug=settings.DEMO_TRACK_SLUG)
        except ObjectDoesNotExist:
            context['demo_track'] = None

        upload_tracks = self.request.session.get("upload_tracks", [])

        context["uploaded_tracks"] = GPXFile.objects.all().filter(slug__in=upload_tracks)

        return context

    def get_success_url(self):

        gpx_file_load_into_database.delay(self.object.pk)

        upload_tracks = self.request.session.get("upload_tracks", [])
        upload_tracks.append(self.object.slug)
        self.request.session["upload_tracks"] = upload_tracks

        return super().get_success_url()


class GPXFileDetailView(DetailView):
    template_name = 'gpx_track_detail.html'
    model = GPXFile

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)
        except Http404:
            messages.add_message(self.request, messages.WARNING, "Track does not longer exists, upload a new...")

            return redirect('/')

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['waypoint_types'] = GPXWayPointType.objects.all()
        return context


class GPXTrackWaypointUpdateView(UpdateView):
    # FIXME hier auch auf slug prüfen
    model = GPXTrackWayPoint
    template_name = 'foo'
    fields = ['hidden']

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse({"status": "ok"})


class GPXTrackDownloadView(FormView):
    template_name = 'foo'
    form_class = GPXTrackWayPointDownload

    def form_valid(self, form):

        waypoint_types = form.cleaned_data.get('waypoint_types', [1, 2, 3])
        slug = form.cleaned_data.get('slug')
        self.object = GPXFile.objects.get(slug=slug)

        r = HttpResponse(self.object.generate_download_gpx_file(waypoint_types), headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": 'attachment; filename="waypoints.gpx"',
        })

        return r


class WaypointDetailView(DetailView):
    model = GPXTrackWayPoint
    template_name = '_waypoint_detail.html'

    def get_object(self, queryset=None):
        gpx_file = GPXFile.objects.get(slug=self.kwargs.get('slug', None))
        object = GPXTrackWayPoint.objects.get(gpx_file=gpx_file, pk=self.kwargs.get('pk', None))

        return object


class GPXFileUserSegmentSplitView(DetailView):
    model = GPXFile
    template_name = '_track_split.html'


class GPXFileUserSegmentSplitDownloadView(DetailView):
    model = GPXFileUserSegmentSplit

    def get_object(self, queryset=None):
        gpx_file = GPXFile.objects.get(slug=self.kwargs.get('slug', None))
        object = GPXFileUserSegmentSplit.objects.get(gpx_file=gpx_file, pk=self.kwargs.get('pk', None))

        return object

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        r = HttpResponse(self.object.generate_gpx(), headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.name}.gpx"',
        })

        return r


class GPXWayPointPathFromTrackDownloadView(DetailView):
    model = GPXTrackWayPoint

    def get_object(self, queryset=None):
        gpx_file = GPXFile.objects.get(slug=self.kwargs.get('slug', None))
        object = GPXTrackWayPoint.objects.get(gpx_file=gpx_file, pk=self.kwargs.get('pk', None))

        return object

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.track_to_waypoint
        except ObjectDoesNotExist:
            return HttpResponse()

        r = HttpResponse(self.object.track_to_waypoint.get_gpx_track(), headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.name}.gpx"',
        })

        return r
