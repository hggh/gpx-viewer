"""
URL configuration for gpxviewr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from baseweb.views import (
    RobotsTxtView,
    GPXFileDetailView,
    GPXTrackDownloadView,
    GPXFileUserSegmentSplitDownloadView,
    GPXTrackWaypointUpdateView,
    GPXWayPointPathFromTrackDownloadView,
    IndexView,
)

from baseweb.viewset import (
    GPXFileViewSet,
)

router = DefaultRouter()
router.register(r'gpxfile', GPXFileViewSet, basename='gpxfile')

urlpatterns = [
    path('api/', include(router.urls)),
    path('robots.txt', RobotsTxtView.as_view(), name='robots'),
    path('', IndexView.as_view(), name='root'),
    path('gpxtrack/<slug:slug>', GPXFileDetailView.as_view(), name='gpx-file-detail'),
    path('gpxtrack/<slug:slug>/download', GPXTrackDownloadView.as_view(), name='gpx-track-download-detail'),
    path('gpxtrack/<slug:slug>/download_gpx_track_to_waypoint/<int:pk>', GPXWayPointPathFromTrackDownloadView.as_view()),
    path('gpxtrack/<slug:slug>/user_segment_split_download/<int:pk>', GPXFileUserSegmentSplitDownloadView.as_view()),
    path('waypoint/<int:pk>/update', GPXTrackWaypointUpdateView.as_view(), name='waypoint-update'),
    path('admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
