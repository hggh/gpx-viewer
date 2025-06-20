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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views

from baseweb.views import (
    StatusView,
    RobotsTxtView,
    GPXFileListView,
    GPXFileDetailView,
    GPXFileEditView,
    GPXTrackDownloadView,
    GPXFileUserSegmentSplitDownloadView,
    GPXFileUserSegmentSplitView,
    GPXWayPointPathFromTrackDownloadView,
    WaypointDetailView,
    IndexView,
)

from baseweb.viewset import (
    GPXFileViewSet,
    GPXWayPointTypeViewSet,
)

from gcollection.views import (
    GCollectionDetailView,
    GCollectionDetailOGImageView,
    GCollectionDetailTokenAuthFailedView,
    GCollectionListView,
    GCollectionCreateView,
    GCollectionShareDeleteView,
    GCollectionShareCreateView,
    GCollectionGPXFileDownloadView,
    GCollectionLogoutView,
    GCollectionLoginView,
    GCollectionProfileView,
)

from gcollection.viewset import (
    GCollectionViewSet,
    GCollectionGPXFileViewSet,
    GCollectionWaypointViewSet,
)

router = DefaultRouter()
router.register(r'gpxfile', GPXFileViewSet, basename='gpxfile')
router.register(r'gpxwaypointtype', GPXWayPointTypeViewSet)
router.register(r'gc', GCollectionViewSet)
router.register(r'gc-gpxfile', GCollectionGPXFileViewSet)
router.register(r'gc-waypoint', GCollectionWaypointViewSet)

urlpatterns = [
    path('social/', include('social_django.urls', namespace="social")),
    path('api/', include(router.urls)),
    path('robots.txt', RobotsTxtView.as_view(), name='robots'),
    path('status', StatusView.as_view(), name='status'),
    path('', IndexView.as_view(), name='root'),
    path('gpxtrack/<slug:slug>', GPXFileDetailView.as_view(), name='gpx-file-detail'),
    path('gpxtrack/<slug:slug>/edit', GPXFileEditView.as_view(), name='gpx-file-edit'),
    path('gpxtrack/<slug:slug>/track_splits', GPXFileUserSegmentSplitView.as_view()),
    path('gpxtrack/<slug:slug>/waypoint/<int:pk>', WaypointDetailView.as_view()),
    path('gpxtrack/<slug:slug>/download', GPXTrackDownloadView.as_view(), name='gpx-track-download-detail'),
    path('gpxtrack/<slug:slug>/download_gpx_track_to_waypoint/<int:pk>', GPXWayPointPathFromTrackDownloadView.as_view()),
    path('gpxtrack/<slug:slug>/user_segment_split_download/<int:pk>', GPXFileUserSegmentSplitDownloadView.as_view()),
    path('gpxtrack/', GPXFileListView.as_view(), name='gpx_file_list'),
    path('gc/token-auth-failed', GCollectionDetailTokenAuthFailedView.as_view(), name='gcollection_token_failed'),
    path('gc/', GCollectionListView.as_view(), name='gcollection_list'),
    path('gc/<int:pk>', GCollectionDetailView.as_view(), name='gcollection_detail'),
    path('gc/<int:pk>/og_image.jpg', GCollectionDetailOGImageView.as_view(), name='gcollection_detail_og_image'),
    path('gc/add', GCollectionCreateView.as_view(), name='gcollection_create'),
    path('gc_share/<int:pk>/delete', GCollectionShareDeleteView.as_view(), name='gc_share_delete'),
    path('gc_share/add', GCollectionShareCreateView.as_view(), name='gc_share_create'),
    path('accounts/login/', GCollectionLoginView.as_view(), name='login'),
    path('accounts/logout/', GCollectionLogoutView.as_view(), name='logout'),
    path('accounts/profile/', GCollectionProfileView.as_view(), name='profile'),
    path('gc_gpx_file/<int:pk>/download', GCollectionGPXFileDownloadView.as_view(), name="gc_gpx_file_download"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
