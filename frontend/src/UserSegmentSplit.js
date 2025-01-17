import L from "leaflet";

export default class UserSegmentSplit {
    constructor(gpx_file_slug, map) {
        this.gpx_file_slug = gpx_file_slug;
        this.map = map;
        this.data = [];
        this._markers = [];
        this._layer = L.layerGroup().addTo(this.map);

        this.get_data();
    }

    get_url() {
        return "/api/gpxfile/" + this.gpx_file_slug + "/user_segment_splits/";
    }
    draw_markers() {
        this._layer.clearLayers();

        this.data.forEach(s => {
            var start = L.marker([s.start.lat, s.start.lon], {
                icon: L.icon({
                    iconUrl: '/static/marker_start.svg',
                    iconSize: [20, 32],
                })
            });
            start.bindPopup("Start: " + s.name);
            start.addTo(this._layer);

            this._markers[s.id + "_start"] = start;
        });
    }

    get_data() {
        var instance = this;
        var r = new XMLHttpRequest();
        r.open('POST', this.get_url());

        r.addEventListener('load', function(event) {
            instance.data = JSON.parse(r.responseText);

            instance.draw_markers();
        });
        r.send()
    }
}
