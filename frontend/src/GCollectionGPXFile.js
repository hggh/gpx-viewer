import L from "leaflet";

export default class GCollectionGPXFile {
    constructor(map, gcollection_pk, gpx_file_pk) {
        this.map = map;
        this.gcollection_pk = gcollection_pk;
        this.gpx_file_pk = gpx_file_pk;

        this.init();
    }

    get_url() {
        let url = "/api/gc/" + this.gcollection_pk + "/gpx_file/" +  this.gpx_file_pk;
        const urlParams = new URLSearchParams(window.location.search);

        if (urlParams.has('token')) {
            url += "?token=" + urlParams.get('token');
        }
        return url;
    }

    async init() {
        var r = new XMLHttpRequest();
        var instance = this;
        r.open('GET', this.get_url());
        r.addEventListener("load", function() {
            instance.draw(this.responseText);
        });
        r.send();
    }

    draw(content) {
        var data = JSON.parse(content);
        let track_html_color = "#3f31f9";
        if (this.gpx_file_pk % 2 == 0) {
            track_html_color = "#ff33cc";
        }

        data.json.forEach((track) => {
            track.segments.forEach((segment) => {
                let points = [];
                segment.points.forEach((point) => {
                    points.push([point.lat, point.lon]);
                });
    
                let line = L.polyline(points, {'color': track_html_color, 'opacity': 0.7}).addTo(this.map);
    
                line.addEventListener("click", (event) => {
                    L.popup()
                        .setLatLng(event.latlng)
                        .setContent(data.name + "<br/>" + "distance: " + Math.round(track.distance / 1000) + " km")
                        .openOn(this.map);
                });
            });
        });       
    }
}