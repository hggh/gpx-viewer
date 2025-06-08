from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DeleteView, CreateView
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect

from gcollection.models import GcollectionShare, GCollection
from gcollection.forms import GcollectionShareForm


class GCollectionShareDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = GcollectionShare

    def test_func(self):
        obj = self.get_object()
        if obj:
            if obj.gcollection.user == self.request.user:
                return True

        return False

    def get_success_url(self):
        return self.object.gcollection.get_absolute_url() + "#share"


class GCollectionShareCreateView(LoginRequiredMixin, CreateView):
    model = GcollectionShare
    form_class = GcollectionShareForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return self.object.gcollection.get_absolute_url() + "#share"
