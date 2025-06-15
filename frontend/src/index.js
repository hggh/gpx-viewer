import 'bootstrap/dist/css/bootstrap.min.css';
import 'leaflet/dist/leaflet.css';
import 'leaflet-sidebar/src/L.Control.Sidebar.css';
import "./style.css";


import L from "leaflet";
import * as d3 from "d3";
import * as bootstrap from "bootstrap";
import Cookies from 'js-cookie';
import sidebar from "leaflet-sidebar";

import "./leaflet.almostover";
import SplitTrackMenu from "./SplitTrackMenu";
import Waypoints from "./Waypoints";
import TrackSegment from "./TrackSegment";
import MapQueryGoogleMaps from "./MapQueryGoogleMaps";
import MapQueryOpenStreetMap from "./MapQueryOpenStreetMap";
import GPXFileStatus from "./GPXFileStatus";
import GPXWayPointTypeStorage from "./GPXWayPointTypeStorage";
import TrackSplitGraph from "./TrackSplitGraph";
import GCollectionGPXFile from "./GCollectionGPXFile";
import GCollectionWaypoint from "./GCollectionWaypoint";


document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("gcollection_pk")) {
        const gcollection_pk = document.getElementById("gcollection_pk").dataset.pk;
        document.getElementById('map').style.height = window.innerHeight - 120 + "px";
        const map = L.map('map').setView([51.505, 10.09], 4);
        const tiles = L.tileLayer('https://tile.openstreetmap.de/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);

        

        L.Control.WayPointContainer = L.Control.extend({
            options: {
                position: "topleft",
            },
            onAdd: function(map) {
                var sidebar = L.control.sidebar('sidebar', {
                    position: 'left'
                });
                
                map.addControl(sidebar);

                let container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                container.title = "Manage Waypoints";
                let button = L.DomUtil.create('a', 'leaflet-control-button', container);
                let img = L.DomUtil.create('img', '', button);
                img.src = '/static/bootstrap-icons-1.11.2/balloon-fill.svg';
                
                L.DomEvent.disableClickPropagation(button);
                L.DomEvent.on(button, 'click', function(){
                    console.log('click');
                    sidebar.toggle();
                });
                console.log(this.options);

                

                return container;
            },
            onRemove: function(map) {},
        });
        let control = new L.Control.WayPointContainer({'options': {'bar': 'foo'}});
        control.addTo(map);

        if (document.getElementById("wp_create_button_create")) {
            let wp_create_button_create = document.getElementById("wp_create_button_create");
            wp_create_button_create.addEventListener("click", (event) => {
                event.target;
                document.getElementById("map").style.cursor = 'crosshair';
            });
        }

        if (document.getElementById("modal_gc_share")) {
            if (window.location.href.indexOf("#share") > -1) {
                let b = new bootstrap.Modal(document.getElementById("modal_gc_share"));
                b.toggle();
            }
        }

        const urlParams = new URLSearchParams(window.location.search);
        let url = '/api/gc/' + gcollection_pk;
        if (urlParams.has('token')) {
            url += "?token=" + urlParams.get('token');
        }

        function gc_gpx_file_upload_wait(gc_gpx_file_id) {
            let timer = setTimeout(gc_gpx_file_upload_wait, 1500, gc_gpx_file_id);

            let r = new XMLHttpRequest();
            r.open('GET', "/api/gc-gpxfile/" + gc_gpx_file_id + "/");
            r.addEventListener("load", function() {
                let data = JSON.parse(r.responseText);

                if (data.job_status >= 10) {
                    clearTimeout(timer);
                    location.reload();
                }
            });
            r.send();
        }

        document.getElementById("modal_gc_gpx_file_add_button").addEventListener("click", (event) => {
            let button = event.currentTarget;
            button.disabled = true;

            let formdata = new FormData();
            let gcollection_id_field = document.getElementById("gc_gpx_file_add_collection_id");
            let gc_gpx_file_name_field = document.getElementById("gc_gpx_file_name");
            let gc_gpx_file_file_field = document.getElementById("gc_gpx_file_file");
            let modal_gc_gpx_file_upload = document.getElementById("modal_gc_gpx_file_upload");
            let gc_gpx_file_date_field = document.getElementById("gc_gpx_file_date");

            modal_gc_gpx_file_upload.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';

            formdata.append("gcollection", gcollection_id_field.value);
            formdata.append("name", gc_gpx_file_name_field.value);
            formdata.append("file", gc_gpx_file_file_field.files[0]);
            formdata.append("date", gc_gpx_file_date_field.value);

            let r = new XMLHttpRequest();
            r.open('POST', "/api/gc-gpxfile/");
            r.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
            r.addEventListener("load", function() {
                let data = JSON.parse(r.responseText);
                if (r.status == 200) {
                    document.getElementById("form_gc_gpx_file_add").reset();

                    gc_gpx_file_upload_wait(data.id);
                }
                else {
                    if (data.errors) {
                        button.disabled = false;
                        modal_gc_gpx_file_upload.innerHTML = data.errors;
                        
                    }
                }
            });
            r.send(formdata);

        });

        try {
            d3.json(url).then(function (data) {
                data.gpx_files.forEach(gpx_file_pk => {
                    new GCollectionGPXFile(map, gcollection_pk, gpx_file_pk);

                });

                new GCollectionWaypoint(map, gcollection_pk, data.waypoints);

                if (data.gpx_files.length == 0) {
                    let m = new bootstrap.Modal(document.getElementById("modal_gc_gpx_file_add"));
                    m.toggle();
                }

                if (data.bounds) {
                    try {
                        map.fitBounds(data.bounds);
                    }
                    catch(err) {

                    }
                }
                
            });
        } catch (error) {
            console.log(error);
        }

        document.querySelectorAll('.gc-gpx-file-delete').forEach((box) => {
            box.addEventListener("click", (event) => {
                let t = event.currentTarget;

                let gpx_file_pk = t.dataset.id;
                if (gpx_file_pk) {
                    document.getElementById("modal_delete_title").innerHTML = t.dataset.name;
                    let myModal = new bootstrap.Modal(document.getElementById("modal_delete"));
                    myModal.toggle()

                    let b = document.getElementById("modal_delete_button");
                    b.addEventListener("click", (event) => {
                        b.disabled = true;
                        document.getElementById("modal_delete_button_close").disabled = true;
                        document.getElementById("modal_delete_body").innerHTML = '<div class="spinner-border text-primary" role="status"></div>';

                        let r = new XMLHttpRequest();
                        r.open('DELETE', "/api/gc-gpxfile/" + gpx_file_pk + "/");
                        r.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
                        r.addEventListener("load", function() {
                            if (this.status == 204) {
                                location.reload();
                            }
                            else {
                                document.getElementById("modal_delete_body").innerHTML = this.responseText;
                            }
                        });
                        r.send();
                    });
                }
            })
        });

    }

    if (document.getElementById("gpx_file_slug")) {
        document.getElementById('map').style.height = window.innerHeight - 120 + "px";

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
                        index += 1;
                    });
                });
                if (index > 1) {
                    document.getElementById('elevation_tab_previous').classList.remove("collapse");
                    document.getElementById('elevation_tab_next').classList.remove("collapse");
                }
            });
        } catch (error) {
            console.log(error);
        }

        // Track Split stuff
        try {
            d3.json('/api/gpxfile/' + gpx_file_slug + '/json').then(function (data) {
                data.forEach(track => {
                    track.segments.forEach(segment => {
                        var f = new TrackSplitGraph(gpx_file_slug, segment.segment_id, map, segment, track.name);
                        f.download_data();
                    });
                });
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

        let gpx_file_status = new GPXFileStatus(map, gpx_file_slug, waypoints);
        gpx_file_status.get_status();

        document.querySelector("#waypoint_icon_size").addEventListener("input", (event) => {
            let icon_size = parseInt(event.target.value);
            waypoints.draw(icon_size);
        });


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
    }

    var f = document.querySelector("#gpx_track_upload")
    if (f) {
        var waypoint_type = new GPXWayPointTypeStorage();
        waypoint_type.load();
        document.getElementById("waypoint_types_reset_to_default").addEventListener("click", (event) => {
            waypoint_type.reset_defaults();
            waypoint_type.store();
        });
        f.onsubmit = function() {
            waypoint_type.store();

            var data = {};
            var waypoint_types = document.querySelectorAll('.waypoint_types');
            for (var i =0; i < waypoint_types.length; i++) {
                var name = waypoint_types[i].dataset.wptName;
                var name_html = waypoint_types[i].dataset.wptNameHtml;
                data[name] = {
                    'enabled': document.querySelector("#" + name_html).checked,
                    'around': document.querySelector("#" + name_html + "_around").value,
                    'around_duplicate': document.querySelector("#" + name_html + "_around_duplicate").value
                };
            }
            document.querySelector("#wpt_options").value = JSON.stringify(data);
        };
    }
});
