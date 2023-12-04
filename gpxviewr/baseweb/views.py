from typing import Any
from django import http
from django.forms.forms import BaseForm
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, DetailView, FormView, UpdateView
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse

from .models import (
    GPXFile,
    GPXTrack,
    GPXWayPointType,
    GPXTrackWayPoint,
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

        upload_tracks = self.request.session.get("upload_tracks", [])

        context["uploaded_tracks"] = GPXFile.objects.all().filter(slug__in=upload_tracks)

        return context

    def get_success_url(self):

        gpx_file_load_into_database.delay(self.object.pk)

        upload_tracks = self.request.session.get("upload_tracks", [])
        upload_tracks.append(self.object.slug)
        self.request.session["upload_tracks"] = upload_tracks

        return super().get_success_url()


class GPXTrackDetailView(DetailView):
    template_name = 'gpx_track_detail.html'
    model = GPXFile

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['waypoint_types'] = GPXWayPointType.objects.all()
        return context


class GPXTrackWaypointView(DetailView):
    template_name = 'foo'
    model = GPXFile

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()

        waypoints_data = []
        for w in self.object.waypoints.all():
            waypoints_data.append(w.get_json_data())

        waypoint_types_data = []
        for wt in GPXWayPointType.objects.all():
            waypoint_types_data.append(wt.get_json_data())

        return JsonResponse({"waypoints": waypoints_data, "waypoint_types": waypoint_types_data})


class GPXTrackWaypointUpdateView(UpdateView):
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

        gpx_file = self.object.generate_download_gpx_file(waypoint_types)

        r = FileResponse(gpx_file, as_attachment=True, filename='waypoints.gpx')
        r['Content-Disposition'] = 'attachment; filename={0}'.format("waypoints.gpx")

        return r
