import L from "leaflet";
import * as bootstrap from "bootstrap";

export default class Waypoints {
    constructor(gpx_file_slug, map) {
        this.map = map;
        this.gpx_file_slug = gpx_file_slug;

        this.leaflet_layers = new Map();
        this.waypoints = new Map();
    }
    remove() {
        this.leaflet_layers.forEach(layer => {
            layer.layer.remove()
        });

        delete this.leaflet_layers;
        delete this.waypoints;

        this.leaflet_layers = new Map();
        this.waypoints = new Map();
    }

    show_route_to(waypoint_pk) {
        var instance = this;
        var url = '/api/gpxfile/' + this.gpx_file_slug + '/geojson_track_to_waypoint/';
        var r = new XMLHttpRequest();
        r.open('POST', url);
        r.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        r.addEventListener('load', function(event) {
            if (r.status == 200) {
                var d = JSON.parse(r.responseText);
                var geojson = L.geoJSON(d, {style: function (feature) {
                    return {
                        color: feature.properties.color,
                        weight: feature.properties.weight,
                        opacity: feature.properties.opacity,
                    };
                }});
                geojson.addTo(instance.map);
            }
        });
        r.send(JSON.stringify({"waypoint_pk": waypoint_pk}));
    }

    draw(icon_size=16) {
        this.remove();

        this.data.waypoints.forEach(waypoint => {
            if (this.leaflet_layers.has(waypoint.waypoint_type.name) == false) {
                let layer = L.layerGroup()
                layer.addTo(this.map);
                this.leaflet_layers.set(waypoint.waypoint_type.name, {"name": waypoint.waypoint_type.name, "layer": layer})
            }
            let leaflet_layer = this.leaflet_layers.get(waypoint.waypoint_type.name);

            let marker = L.marker([waypoint.lat, waypoint.lon]);
            marker.waypointId = waypoint.id;
            marker.setIcon(L.icon({
                iconSize: [icon_size, icon_size],
                iconUrl: waypoint.waypoint_type.marker_image_path,
                className: waypoint.class_name,
            }));
            if (waypoint.has_gpx_track_to == true) {
                marker.addEventListener("popupopen", (event) => {
                    this.show_route_to(event.target.waypointId);
                });
            }

            marker.bindPopup('Loading...').openPopup();
            marker.addEventListener("popupopen", event => {
                var waypoint_id = event.target.waypointId;
                var marker_event = event.target;

                let r = new XMLHttpRequest();
                r.open('GET', "/gpxtrack/" +  this.gpx_file_slug + "/waypoint/" + waypoint_id);

                r.addEventListener('load', function(event) {
                    marker_event.setPopupContent(r.responseText);
                    marker_event.update();

                });
                r.send()
            });

            marker.addTo(leaflet_layer.layer);
            this.waypoints.set(waypoint.id, marker)
        });
    }

    get_url() {
        return "/api/gpxfile/" + this.gpx_file_slug + "/waypoints/";
    }

    get_data() {
        var instance = this;
        var r = new XMLHttpRequest();
        r.open('POST', this.get_url());

        r.addEventListener('load', function(event) {
            instance.data = JSON.parse(r.responseText);

            instance.draw();

        });
        r.send()
    }
}
