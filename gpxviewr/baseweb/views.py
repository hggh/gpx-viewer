from typing import Any
from django import http
from django.shortcuts import redirect
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.db import models
from django.forms.forms import BaseForm
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView, CreateView, DetailView, FormView, UpdateView, View, ListView
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
    GPXFileUploadForm,
    GPXFileUpdateForm,
)

from .tasks import gpx_file_load_into_database


class StatusView(View):
    def get(self, request, *args, **kwargs):
        errors = GPXFile.objects.filter(job_status=5)

        if errors:
            return HttpResponse("Error", status=404)

        return HttpResponse("OK")


class RobotsTxtView(TemplateView):
    template_name = 'robots.txt'
    content_type = 'text/plain'


class IndexView(CreateView):
    template_name = 'index.html'
    model = GPXFile
    form_class = GPXFileUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        initial['user'] = self.request.user

        return initial

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


class GPXFileListView(LoginRequiredMixin, ListView):
    model = GPXFile
    template_name = 'gpx_file_list.html'

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class GPXFileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = 'gpx_track_edit.html'
    model = GPXFile
    form_class = GPXFileUpdateForm

    def test_func(self):
        if self.request.user.is_authenticated and self.get_object().user == self.request.user:
            return True
        return False


class GPXFileDetailView(UserPassesTestMixin, DetailView):
    template_name = 'gpx_track_detail.html'
    model = GPXFile

    def test_func(self):
        try:
            self.get_object()
        except Http404:
            messages.add_message(self.request, messages.WARNING, "Track does not longer exists, upload a new...")

            return redirect('/')

        if self.get_object().perm_public_available is False:
            if self.request.user and self.request.user.is_authenticated and self.get_object().user == self.request.user:
                return True
            else:
                return False

        return True

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['waypoint_types'] = GPXWayPointType.objects.all()
        return context


class GPXTrackDownloadView(UserPassesTestMixin, DetailView):
    model = GPXFile

    def test_func(self):
        if self.get_object().perm_public_available is False:
            if self.request.user.is_authenticated and self.get_object().user == self.request.user:
                return True
            else:
                return False
        else:
            return True

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        include_waypoints_types = {}
        for wpt in self.object.get_waypoint_types():
            include_waypoints_types.update({
                wpt.name: {
                    'state': self.request.GET.get(wpt.name, 'off') == 'on',
                    'bookmark': self.request.GET.get(f"{wpt.name}_bookmark", 'off') == 'on',
                    'wp_mode_garmin': self.request.GET.get('wp_mode_garmin', 'off') == 'on',
                    'wp_mode_orginal': self.request.GET.get('wp_mode_orginal', 'off') == 'on',
                }
            })

        r = HttpResponse(self.object.generate_download_gpx_file(include_waypoints_types), headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.file.name}"',
        })

        return r


class WaypointDetailView(UserPassesTestMixin, DetailView):
    model = GPXTrackWayPoint
    template_name = '_waypoint_detail.html'

    def test_func(self):
        self.get_object()
        if self.gpx_file.perm_public_available is False:
            if self.request.user.is_authenticated and self.gpx_file.user == self.request.user:
                return True
            else:
                return False
        else:
            return True

    def get_object(self, queryset=None):
        self.gpx_file = GPXFile.objects.get(slug=self.kwargs.get('slug', None))
        object = GPXTrackWayPoint.objects.get(gpx_file=self.gpx_file, pk=self.kwargs.get('pk', None))

        return object


class GPXFileUserSegmentSplitView(UserPassesTestMixin, DetailView):
    model = GPXFile
    template_name = '_track_split.html'

    def test_func(self):
        if self.get_object().perm_public_available is False:
            if self.request.user.is_authenticated and self.get_object().user == self.request.user:
                return True
            else:
                return False

        return True


class GPXFileUserSegmentSplitDownloadView(UserPassesTestMixin, DetailView):
    model = GPXFileUserSegmentSplit

    def test_func(self):
        gpx_file = self.get_object().gpx_file

        if gpx_file.perm_public_available is False:
            if self.request.user.is_authenticated and gpx_file.user == self.request.user:
                return True
            else:
                return False
        else:
            return True

    def get_object(self, queryset=None):
        gpx_file = GPXFile.objects.get(slug=self.kwargs.get('slug', None))
        object = GPXFileUserSegmentSplit.objects.get(gpx_file=gpx_file, pk=self.kwargs.get('pk', None))

        return object

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        include_waypoints_types = {}
        include_waypoints = self.request.GET.get('include_waypoints', '0') == '1'

        if include_waypoints is True:
            for wpt in self.object.gpx_file.get_waypoint_types():
                include_waypoints_types.update({
                    wpt.name: {
                        'state': self.request.GET.get(wpt.name, 'off') == 'on',
                        'bookmark': self.request.GET.get(f"{wpt.name}_bookmark", 'off') == 'on',
                        'wp_mode_garmin': self.request.GET.get('wp_mode_garmin', 'off') == 'on',
                        'wp_mode_orginal': self.request.GET.get('wp_mode_orginal', 'off') == 'on',
                    }
                })

        r = HttpResponse(self.object.generate_gpx(include_waypoints=include_waypoints, include_waypoints_types=include_waypoints_types), headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.name}.gpx"',
        })

        return r


class GPXWayPointPathFromTrackDownloadView(UserPassesTestMixin, DetailView):
    model = GPXTrackWayPoint

    def test_func(self):
        gpx_file = self.get_object().gpx_file

        if gpx_file.perm_public_available is False:
            if self.request.user.is_authenticated and gpx_file.user == self.request.user:
                return True
            else:
                return False
        else:
            return True

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
