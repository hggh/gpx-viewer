from django.contrib import admin

from baseweb.models import (
    GPXTrack,
    GPXTrackWayPoint,
    GPXTrackSegmentPoint,
)


class GPXTrackAdmin(admin.ModelAdmin):
    pass


class GPXTrackWayPointAdmin(admin.ModelAdmin):
    pass


class GPXTrackSegmentPointAdmin(admin.ModelAdmin):
    pass


admin.site.register(GPXTrack, GPXTrackAdmin)
admin.site.register(GPXTrackWayPoint, GPXTrackWayPointAdmin)
admin.site.register(GPXTrackSegmentPoint, GPXTrackSegmentPointAdmin)
