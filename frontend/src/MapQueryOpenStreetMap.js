import L from "leaflet";

export default class MapQueryOpenStreetMap {
    constructor(map) {
        this.map = map;
        this.feature_active = false;
        this.displayed = false;
        this.info_box = document.getElementById("map_query_opensteetmap_info_message_box");

        this.map.on("click", this.onclick_map.bind(this));

        document.querySelector("#map_query_openstreetmap").addEventListener("click", (event) => {
            if (this.displayed == false) {
                this.info_box.classList.add('in');
                setTimeout(this.remove_info_box.bind(this), 1600);
                // display Info Box only once
                this.displayed = true;
            }

            this.feature_active = true;
            document.getElementById('map').style.cursor = 'crosshair';
        });
    }
    onclick_map(e) {
        if (this.feature_active == true) {
            this.feature_active = false;
            
            document.getElementById('map').style.cursor = '';
            window.open(
                "https://www.openstreetmap.org/query?lat=" + e.latlng.lat + "&lon=" + e.latlng.lng + "#map=14/" + e.latlng.lat + "/" + e.latlng.lng,
                "_blank"
        );
        }
    }
    remove_info_box() {
        this.info_box.classList.remove('in');
    }
}