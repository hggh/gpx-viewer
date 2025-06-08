from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from gcollection.forms import GCollectionProfileDeleteForm


class GCollectionLogoutView(auth_views.LogoutView):
    next_page = '/accounts/login/'


class GCollectionLoginView(auth_views.LoginView):
    next_page = '/gc'


class GCollectionProfileView(LoginRequiredMixin, TemplateView, FormView):
    template_name = 'registration/profile.html'
    form_class = GCollectionProfileDeleteForm
    success_url = '/accounts/login'

    def form_valid(self, form):
        for gcollection in self.request.user.gcollections.all():
            for gpx_file in gcollection.gpx_files.all():
                gpx_file.delete()
            gcollection.delete()

        self.request.user.delete()

        return super().form_valid(form)
