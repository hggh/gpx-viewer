from django.contrib import admin

from baseweb.models import (
    GPXFile,
    GPXTrack,
    GPXTrackWayPoint,
    GPXTrackSegmentPoint,
)


class GPXFileAdmin(admin.ModelAdmin):
    pass


class GPXTrackAdmin(admin.ModelAdmin):
    pass


class GPXTrackWayPointAdmin(admin.ModelAdmin):
    pass


class GPXTrackSegmentPointAdmin(admin.ModelAdmin):
    pass


admin.site.register(GPXTrack, GPXTrackAdmin)
admin.site.register(GPXTrackWayPoint, GPXTrackWayPointAdmin)
admin.site.register(GPXTrackSegmentPoint, GPXTrackSegmentPointAdmin)
admin.site.register(GPXFile, GPXFileAdmin)
