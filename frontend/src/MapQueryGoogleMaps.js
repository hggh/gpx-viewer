import L from "leaflet";

export default class MapQueryGoogleMaps {
    constructor(map) {
        this.map = map;
        this.feature_active = false;
        this.displayed = false;
        this.info_box = document.getElementById("map_query_google_maps_info_message_box");

        this.map.on("click", this.onclick_map.bind(this));

        document.querySelector("#map_query_google_maps").addEventListener("click", (event) => {
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
                "https://www.google.com/maps/@" + e.latlng.lat + "," + e.latlng.lng + ",17z?entry=ttu",
                "_blank"
            );
        }
    }
    remove_info_box() {
        this.info_box.classList.remove('in');
    }
    
}