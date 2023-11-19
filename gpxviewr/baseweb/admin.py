from django.contrib import admin

from baseweb.models import (
    GPXTrack,
    GPXTrackWayPoint,
)


class GPXTrackAdmin(admin.ModelAdmin):
    pass


class GPXTrackWayPointAdmin(admin.ModelAdmin):
    pass


admin.site.register(GPXTrack, GPXTrackAdmin)
admin.site.register(GPXTrackWayPoint, GPXTrackWayPointAdmin)
