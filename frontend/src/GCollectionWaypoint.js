import L from "leaflet";

export default class GCollectionWaypoint {
    constructor(map, gcollection_pk, waypoints) {
        this.map = map;
        this.gcollection_pk = gcollection_pk;
        this.waypoints = waypoints;
        this.marker = null;
        this.layer = L.layerGroup().addTo(this.map);

        this.init();
    }

    async init() {
        this.waypoints.forEach(waypoint => {
            let marker = L.marker([waypoint.location.lat, waypoint.location.lng], {
                icon: L.icon({
                    iconUrl: '/static/gcollection/' + waypoint.waypoint_type.image_name,
                    iconSize: [30, 35],
                    iconAnchor: [15, 35],
                    popupAnchor: [0, -35],
                }),
            });
            marker.waypoint_pk = waypoint.id;
            marker.addTo(this.layer);
            marker.bindPopup();
            marker.addEventListener("popupopen", event => {
                event.target.setPopupContent(waypoint.name);
            });


            this.waypoints.set(waypoint.id, marker)
        });
        this.marker.addTo(this.layer);
    }
}
