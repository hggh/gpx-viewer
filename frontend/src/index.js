import 'bootstrap/dist/css/bootstrap.min.css';
import 'leaflet/dist/leaflet.css';
import "./style.css";


import L from "leaflet";
import * as d3 from "d3";
import * as bootstrap from "bootstrap";

import "./leaflet.almostover";
import SplitTrackMenu from "./SplitTrackMenu";
import Waypoints from "./Waypoints";
import UserSegmentSplit from "./UserSegmentSplit";
import TrackSegment from "./TrackSegment";
import MapQueryGoogleMaps from "./MapQueryGoogleMaps";
import MapQueryOpenStreetMap from "./MapQueryOpenStreetMap";
import GPXFileStatus from "./GPXFileStatus";


document.addEventListener("DOMContentLoaded", function() {

    document.getElementById('map').style.height = window.innerHeight - 200 + "px";

    const gpx_file_slug = document.getElementById("gpx_file_slug").dataset.slug;
    const map = L.map('map').setView([51.505, 10.09], 3);
    const tiles = L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    document.querySelector("#osm_tile_lang").addEventListener("change", (event) => {
        tiles.setUrl(event.target.value);
    });

    L.Control.ElevationContainer = L.Control.extend({
        options: {
            position: "topright",
            width: 500,
            height: 240,
        },
        onAdd: function(map) {
            this.map = map;
            var div = L.DomUtil.create('div');
            div.id = "map_elevation";
            div.classList.add("map_elevation");

            var tab = document.createElement("div");
            tab.className = "tab-content";
            tab.id = "map_elevation_tabs";

            div.appendChild(tab);

            return div;
        }
    });
    L.Control.elevation = function(opts) {
        return new L.Control.ElevationContainer(opts);
    }
    L.Control.elevation().addTo(map);

    try {
        d3.json('/api/gpxfile/' + gpx_file_slug + '/json').then(function (data) {
            var index = 0;
            var active_tab = true;
            data.forEach(track => {
                track.segments.forEach(segment => {
                    var f = new TrackSegment(gpx_file_slug, segment.segment_id, map, segment, track.name, active_tab, index);
                    active_tab = false;
                });
                index += 1;
            });
            if (index > 1) {
                document.getElementById('elevation_tab_previous').classList.remove("collapse");
                document.getElementById('elevation_tab_next').classList.remove("collapse");
            }
        });
    } catch (error) {
        console.log(error);
    }

    let split_track_menu = new SplitTrackMenu(gpx_file_slug, map, "sidebar_split_track");
    split_track_menu.get_data();

    var waypoints = new Waypoints(gpx_file_slug, map);
    waypoints.get_data();

    let map_query_google_maps = new MapQueryGoogleMaps(map);  
    let map_query_openstreetmap = new MapQueryOpenStreetMap(map);

    let user_segment_split = new UserSegmentSplit(gpx_file_slug, map);

    let gpx_file_status = new GPXFileStatus(map, gpx_file_slug, waypoints);
    gpx_file_status.get_status();


    document.querySelector("#elevation_hide_show").addEventListener("click", (event) => {
        var w = L.DomUtil.get("map_elevation_tabs");
        if (w.classList.contains('collapse')) {
            w.classList.remove('collapse');
        }
        else {
            w.classList.add('collapse');
        }
    });
    document.querySelector("#elevation_tab_next").addEventListener("click", (event) => {
        var tab = document.querySelector("#map_elevation_tabs");
        var tabs = tab.querySelectorAll(".tab-pane");
        for (var i = 0, length = tabs.length; i < length; i++) {
            if (tabs[i].classList.contains('active')) {
                tabs[i].classList.remove('active');
                if (i == tabs.length - 1) {
                    tabs[0].classList.add('active');
                }
                else {
                    tabs[i + 1].classList.add('active');
                }
                break;
            }
        }
    });
    document.querySelector("#elevation_tab_previous").addEventListener("click", (event) => {
        var tab = document.querySelector("#map_elevation_tabs");
        var tabs = tab.querySelectorAll(".tab-pane");
        for (var i = 0, length = tabs.length; i < length; i++) {
            if (tabs[i].classList.contains('active')) {
                tabs[i].classList.remove('active');
                if (i == 0) {
                    tabs[length - 1 ].classList.add('active');
                }
                else {
                    tabs[i - 1].classList.add('active');
                }
                break;
            }
        }
    });

    function hide_elevation_graph() {
        var w = L.DomUtil.get("map_elevation_tabs");
        w.classList.add('collapse');

        var e = L.DomUtil.get("elevation_hide_show");
        e.classList.add("elevation_hide_show_shake");

    }
    // show the elevation graph and then hide it after 1s
    setTimeout(hide_elevation_graph, 1500);

});
