from typing import Any
from django import http
from django.forms.forms import BaseForm
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, DetailView, FormView
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse

from .models import (
    GPXTrack,
    GPXWayPointType,
    generate_default_delete_after_date,
)

from .forms import (
    GPXTrackWayPointDownload,
    GPXTrackUploadForm,
)

from .tasks import gpx_track_query_osm


class RobotsTxtView(TemplateView):
    template_name = 'robots.txt'


class IndexView(CreateView):
    template_name = 'index.html'
    model = GPXTrack
    form_class = GPXTrackUploadForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['waypoint_types'] = GPXWayPointType.objects.all()
        return context

    def get_success_url(self):

        gpx_track_query_osm.delay(self.object.pk)

        return super().get_success_url()


class GPXTrackDetailView(DetailView):
    template_name = 'gpx_track_detail.html'
    model = GPXTrack

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['waypoint_types'] = GPXWayPointType.objects.all()
        return context


class GPXTrackWaypointView(DetailView):
    template_name = 'foo'
    model = GPXTrack

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.object = self.get_object()

        data = []
        for w in self.object.waypoints.all():
            data.append(w.get_json_data())

        return JsonResponse({"waypoints": data})


class GPXTrackDownloadView(FormView):
    template_name = 'foo'
    form_class = GPXTrackWayPointDownload

    def form_valid(self, form):

        waypoint_types = form.cleaned_data.get('waypoint_types', [1, 2, 3])
        slug = form.cleaned_data.get('slug')
        self.object = GPXTrack.objects.get(slug=slug)

        gpx_file = self.object.generate_download_gpx_file(waypoint_types)

        r = FileResponse(gpx_file, as_attachment=True, filename='waypoints.gpx')
        r['Content-Disposition'] = 'attachment; filename={0}'.format("waypoints.gpx")

        return r
