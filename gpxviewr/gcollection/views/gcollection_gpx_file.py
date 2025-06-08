from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse

from gcollection.models import GCollectionGPXFile


class GCollectionGPXFileDownloadView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = GCollectionGPXFile

    def test_func(self):
        if self.request.user == self.get_object().gcollection.user:
            return True

        return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        r = HttpResponse(self.object.file, headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.file.name}"',
        })

        return r
