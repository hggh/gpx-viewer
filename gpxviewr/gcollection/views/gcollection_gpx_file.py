from django.views.generic import DetailView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse

from gcollection.models import GCollectionGPXFile


class GCollectionGPXFileDownloadView(UserPassesTestMixin, DetailView):
    model = GCollectionGPXFile

    def test_func(self):
        if self.request.user:
            if self.request.user == self.get_object().gcollection.user:
                return True

        if (token := self.request.GET.get('token', None)) is not None:
            tokens = self.get_object().gcollection.shares.all().filter(slug=token).filter(valid_until_date__gte=timezone.now())
            if tokens and tokens.count() == 1:
                if tokens.get().perm_download is True:
                    return True

        return False

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        r = HttpResponse(self.object.file, headers={
            "Content-Type": "application/gpx+xml",
            "Content-Disposition": f'attachment; filename="{self.object.file.name}"',
        })

        return r
