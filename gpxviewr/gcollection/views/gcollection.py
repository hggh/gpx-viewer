from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect, FileResponse, Http404

from gcollection.models import GCollection, GCollectionWayPointType
from gcollection.forms import GCollectionForm


class GCollectionDetailTokenAuthFailedView(TemplateView):
    template_name = 'gcollection/token_auth_failed.html'


class GCollectionDetailOGImageView(UserPassesTestMixin, DetailView):
    model = GCollection

    def test_func(self):
        if self.request.user:
            if self.get_object().user == self.request.user:
                return True

        token = self.request.GET.get('token', None)

        if self.get_object().shares.all().filter(slug=token).filter(valid_until_date__gte=timezone.now()).count() > 0:
            return True

        return False

    def get(self, request, *args, **kwargs):
        object = self.get_object()

        if object.has_og_image():
            return FileResponse(open(object.get_og_image_filepath(), 'rb'))

        return Http404()


class GCollectionDetailView(UserPassesTestMixin, DetailView):
    template_name = 'gcollection/detail.html'
    model = GCollection

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            context['waypoint_types'] = GCollectionWayPointType.objects.all()

        return context

    def handle_no_permission(self):
        if self.request.GET.get('token', None):
            return HttpResponseRedirect(reverse('gcollection_token_failed'))
        else:
            return super().handle_no_permission()

    def test_func(self):
        if self.request.user:
            if self.get_object().user == self.request.user:
                return True

        token = self.request.GET.get('token', None)

        if self.get_object().shares.all().filter(slug=token).filter(valid_until_date__gte=timezone.now()).count() > 0:
            return True

        return False


class GCollectionListView(LoginRequiredMixin, ListView):
    template_name = 'gcollection/list.html'
    model = GCollection

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)


class GCollectionCreateView(LoginRequiredMixin, CreateView):
    template_name = 'gcollection/create.html'
    model = GCollection
    form_class = GCollectionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()

        initial['user'] = self.request.user

        return initial
