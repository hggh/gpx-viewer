class SplitTrackMenu {
    constructor(gpx_file_slug, map, sidebar_split_track_id) {
        this.map = map;
        this.gpx_file_slug = gpx_file_slug;
        this.sidebar_split_track_id = sidebar_split_track_id;
    }

    get_url() {
        return '/gpxtrack/' + this.gpx_file_slug + '/track_splits';
    }

    get_data() {
        var instance = this;
        var r = new XMLHttpRequest();
        r.open('GET', this.get_url());
        r.addEventListener('load', function(event) {
            instance.update_data(r.responseText);
        });
        r.send();
    }

    update_data(data) {
        var sidebar_split_track = document.getElementById(this.sidebar_split_track_id);

        sidebar_split_track.innerHTML = data;
    }
}

class Waypoints {
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

    draw() {
        this.remove();

        this.data.waypoints.forEach(waypoint => {
            if (this.leaflet_layers.has(waypoint.waypoint_type.name) == false) {
                var layer = L.layerGroup()
                layer.addTo(this.map);
                this.leaflet_layers.set(waypoint.waypoint_type.name, {"name": waypoint.waypoint_type.name, "layer": layer})
            }
            var leaflet_layer = this.leaflet_layers.get(waypoint.waypoint_type.name);

            var marker = L.marker([waypoint.lat, waypoint.lon]);
            marker.waypointId = waypoint.id;
            marker.setIcon(L.icon({
                iconSize: [16, 16],
                iconUrl: waypoint.waypoint_type.marker_image_path,
                className: waypoint.class_name,
            }));
            if (waypoint.has_gpx_track_to == true) {
                marker.addEventListener("popupopen", (event) => {
                    this.show_route_to(event.target.waypointId);
                });
            }

            if (waypoint.name != "" || waypoint.url != null || waypoint.has_gpx_track_to == true) {
                var content = "";
                if (waypoint.name != "") {
                    content += "<b>" + waypoint.name + "</b><br/>";
                }
                if (waypoint.url != null) {
                    content += "Homepage: <a href='" + waypoint.url + "' target='_blank'>" + waypoint.url + "</a>";
                }
                if (waypoint.has_gpx_track_to == true) {
                    var ln = waypoint.track_to_waypoint.length;
                    content += "<br/><a href='/gpxtrack/"+gpx_file_slug+"/download_gpx_track_to_waypoint/"+waypoint.id+"'>Download Track to WayPoint ("+ln+" km)</a><br/>";
                }
                marker.bindPopup(content).openPopup();
            }
            else {
                marker.bindPopup('').openPopup();
            }

            marker.addEventListener("popupopen", event => {
                
                var waypoint_id = event.target.waypointId;

                var r = new XMLHttpRequest();
                r.open('GET', "/gpxtrack/" +  this.gpx_file_slug + "/waypoint/" + waypoint_id);
                
                r.addEventListener('load', function(event) {
                    var content_top = document.getElementById("canvas_top");
                    content_top.innerHTML = r.responseText;

                    var offcanvasTop = new bootstrap.Offcanvas(document.getElementById("offcanvasTop"));
                    offcanvasTop.show();

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

class TrackSegment {
    constructor(gpx_file_slug, segment_pk, map, segment, track_name, active_tab, index) {
        this.gpx_file_slug = gpx_file_slug;
        this.segment_pk = segment_pk;
        this.map = map;
        this.segment = segment;
        this.tab_element_name = "map_elevation_tabs";
        this.index = index;
        this._marker_movement = true;
        this.segment_split_lines = [];

        this.margin = {
            top: 10,
            bottom: 30,
            right: 30,
            left: 50,
        };
        this.width = 460 - this.margin.left - this.margin.right;
        this.height = 200 - this.margin.top - this.margin.bottom;
        
        this.tab_element = document.createElement("div");
        this.tab_element.id = "graph_tab_" + this.segment_pk;


        if (active_tab) {
            this.tab_element.className = "tab-pane active";
        }
        else {
            this.tab_element.className = "tab-pane";
        }
        this.tab_element.role = "tabpanel";
        this.tab_element.tabindex = "0";

        var text = document.createElement("h5");
        text.innerHTML = track_name;
        this.tab_element.appendChild(text);

        var graph_tab = document.createElement("div");
        graph_tab.id = "graph_" + this.segment_pk;
        this.tab_element.appendChild(graph_tab);

        var box = L.DomUtil.get(this.tab_element_name);
        box.appendChild(this.tab_element);

        this.svg = d3.select(this.get_container_name()).append("svg")
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom)
            .append("g")
            .attr("transform",`translate(${this.margin.left},${this.margin.top})`);

        this.background = this.svg.append("g").attr("class", "group1");
        this.foreground = this.svg.append("g").attr("class", "group2");

        this._marker = L.circleMarker([0, 0], {'color': '#ff0000'}).addTo(this.map);
        this._marker.setRadius(7);

        this._marker.addEventListener("popupclose", (event) => {
            this._marker_movement = true;
        });
        this._marker.bindPopup(this.edit_marker_popup.bind(this));

        this.graph();
        this.draw_line();

        this.get_user_segment_split_data();
    }

    async get_user_segment_split_data() {
        var url = "/api/gpxfile/" + this.gpx_file_slug + "/user_segment_splits/";
        var r = new XMLHttpRequest();
        r.open('POST', url);
        r.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        r.addEventListener("load", (event) => {
            this.user_segment_split_data = JSON.parse(r.responseText);
            this.setup_split_overlay();
        });
        r.send(JSON.stringify({'segment_pk': this.segment_pk}));
    }

    async setup_split_overlay() {
        this.user_segment_split_data.forEach((split) => {
            var data = [];

            this.segment.points.forEach((point) => {
                if (point.point_number >= split.start.number && point.point_number <= split.end.number) {
                    data.push([point.lat, point.lon]);
                }
            });
            this.segment_split_lines[split.id] = L.polyline(data, {'color': 'green', 'opacity': 1});
        });

        document.querySelectorAll(".user-track-splits").forEach(box => {
            box.addEventListener("mouseover", (event) => {
                var id = event.target.parentNode.dataset.id;
                var segment_id = event.target.parentNode.dataset.segmentId;

                if (id && segment_id && parseInt(segment_id) == parseInt(this.segment_pk)) {
                    this.user_segment_split_data.forEach((split) => {
                        if (split.id == parseInt(id)) {
                            this.segment_split_lines[split.id].bringToFront();
                            this.segment_split_lines[split.id].addTo(this.map);
                            this.map.fitBounds(this.segment_split_lines[split.id].getBounds());

                            setTimeout(() => {
                                this.segment_split_lines[split.id].removeFrom(this.map);
                            }, 1000);
                        }
                    });
                }
            });
        });
    }

    edit_marker_popup(layer) {
        this._marker_movement = false;

        var l = L.GeometryUtil.closest(this.map, this.line, layer._latlng, true);
        var s = this.segment.points.findIndex((element) => element.lat == l.lat && element.lon == l.lng);
        var point = this.segment.points[s];

        var split_data_html = null;
        if (this.user_segment_split_data) {
            var split_start = 0;
            for (var split of this.user_segment_split_data) {
                if (point.point_number > split.start.number && split.start.number > split_start) {
                    split_start = split.start.number;
                }
            }
            // FIXME? point number vs Index of Array?
            var distance_last_start = this.segment.points[point.point_number].distance - this.segment.points[split_start].distance;

            var split_data_html = document.createElement("div");
            split_data_html.innerText = "from last Start: " + Math.round(distance_last_start / 1000) + " km";
        }

        var html = document.createElement("div");
        if (split_data_html) {
            html.appendChild(split_data_html);
        }

        var button = document.createElement("button");
        button.innerText = "Split Track here";
        button.className = "btn btn-outline-info";
        button.setAttribute("type", "button");
        button.setAttribute("data-point-number", point.point_number);
        button.setAttribute("data-segment-id", this.segment_pk);
        button.addEventListener("click", (event) => {
            var point_number = event.target.dataset.pointNumber;
            var segment_id = event.target.dataset.segmentId;
            event.target.disabled = true;

            var url = "/api/gpxfile/" + this.gpx_file_slug + "/user_segment_split/";
            var r = new XMLHttpRequest();
            r.open('POST', url);
            r.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            r.addEventListener("load", (event) => {
                location.reload();
            });
            r.send(JSON.stringify({'segment_pk': segment_id, 'point_number': point_number}));
            
        });

        html.appendChild(button);
        return html;
    }

    async draw_line() {
        var data = [];

        this.segment.points.forEach((point) => {
            data.push([point.lat, point.lon]);
        });

        this.line = L.polyline(data, {'color': this.segment.color, 'opacity': 0.7}).addTo(this.map);
        this.map.almostOver.addLayer(this.line);

        this.map.addEventListener("almost:move", (event) => {
            if (this._marker_movement == false) {
                return;
            }
            var result = Infinity;
            var p = null;

            this.segment.points.forEach((point) => {
                var distance = event.latlng.distanceTo([point.lat, point.lon]);
                if (distance < result) {
                    result = distance;
                    p = point;
                }
            });
            var xpos = this.x(p.distance / 1000);

            this.draw_tooltip(xpos, p);
            this._marker.setLatLng(p);
        });
        this.map.fitBounds(this.line.getBounds());
    }

    draw_tooltip(xpos, point) {
        this.xAxisLine.attr("x", xpos);

        var mouse_text_xpos = xpos + 10;
        if (xpos > (this.width / 2)) {
            mouse_text_xpos = xpos - 120;
        }

        this.mouse_text
            .text(Math.round(point.distance / 1000) + " km / " + Math.round(point.elevation) + "m")
            .style("opacity", 1)
            .attr("class", "mouse-text")
            .attr("y", "40")
            .attr("x", mouse_text_xpos);
    }

    get_container_name() {
        return "#graph_" + this.segment_pk;
    }

    pm_mouseover(event) {
        if (this._marker_movement == false) {
            return;
        }

        var [xpos, ypos] = d3.pointer(event);
        this.xAxisLine.attr("x", xpos);

        var mouse_pointer_distance = this.x.invert(xpos);
        var i = d3.bisector((d) => d.distance).right(this.segment.points, (mouse_pointer_distance * 1000));

        this.draw_tooltip(xpos, this.segment.points[i]);

        this._marker.setLatLng([this.segment.points[i].lat, this.segment.points[i].lon]);
    }

    async graph() {
        this.x = d3.scaleLinear();
        this.y = d3.scaleLinear();

        this.xAxisLine = this.foreground.append("g").append("rect")
            .attr("class", "dotted")
            .attr("stroke-with", "1px")
            .attr("width", ".5px")
            .attr("height", this.height);

        this.mouse_text = this.foreground.append("g")
            .append("text")
            .style("opacity", 0)
            .attr("text-anchor", "right");

        const listeningRect = this.foreground
            .append("rect")
            .attr("class", "listening-rect")
            .attr("width", this.width)
            .attr("height", this.height)

        listeningRect.on("mousemove", this.pm_mouseover.bind(this));

        this.x.domain(d3.extent(this.segment.points, d => d.distance / 1000))
            .range([ 0, this.width ]);

        this.background.append("g")
            .attr("transform", `translate(0,${this.height})`)
            .call(d3.axisBottom(this.x));

        this.y.domain([0, d3.max(this.segment.points, d => +d.elevation)])
            .range([ this.height, 0 ]);

        this.background.append("g")
              .call(d3.axisLeft(this.y))
              .call(g => g.append("text")
              .attr("x", -this.margin.left)
              .attr("y", 10)
              .attr("fill", "currentColor")
              .attr("text-anchor", "start")
              .text("m"));

        this.background.append("path")
            .datum(this.segment.points)
            .attr("fill", "#cce5df")
            .attr("stroke", "#69b3a2")
            .attr("stroke-width", 1.5)
            .attr("d", d3.area()
                .x(d => this.x(d.distance / 1000))
                .y0(this.y(0))
                .y1(d => this.y(d.elevation))
            )
    }
}

class MapQueryGoogleMaps {
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

class MapQueryOpenStreetMap {
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

class GPXFileStatus {
    constructor(map, gpx_file_slug, waypoints, job_status_info_id="job_status_info", job_status_info_box_id="job_status_info_box") {
        this.map = map;
        this.waypoints = waypoints;
        this.gpx_file_slug = gpx_file_slug;
        this.job_status_info_id = job_status_info_id;
        this.job_status_info_box_id = job_status_info_box_id;
        this.last_status = null;
        this.gpx_track_loading_finished = false;
        this.reload = false;
        this.round = 0;
    }

    get_url() {
        return "/api/gpxfile/" + this.gpx_file_slug + "/job_status/";
    }

    get_status() {
        var r = new XMLHttpRequest();
        var instance = this;
        r.open('POST', this.get_url());
        r.addEventListener("load", function() {
            instance.status(this.responseText);
        });
        r.send();
    }

    status(r) {
        var d = JSON.parse(r);
        this.reload = false;

        if (this.last_status !== null && (d.finished == true || d.job_status_name == 'error')) {
            location.reload();
            return;
        }
        else if (d.job_status_name == "uploaded") {
            this.reload = true;
            document.getElementById(this.job_status_info_id).classList.remove("collapse");
        }
        else if (d.job_status_name == "gpx_track_loading") {
            this.reload = true;
            document.getElementById(this.job_status_info_id).classList.remove("collapse");
            document.getElementById(this.job_status_info_box_id).innerHTML = "GPX Track is processing";
        }
        else if (d.job_status_name == "osm_query") {
            this.reload = true;
            document.getElementById(this.job_status_info_id).classList.remove("collapse");
            document.getElementById(this.job_status_info_box_id).innerHTML = "OpenStreetMap Query is in progress...";

            if (this.round % 4 == 0) {
                this.waypoints.get_data();
            }
        }
        if (d.job_status_name == "osm_query" && this.gpx_track_loading_finished == false) {
            this.gpx_track_loading_finished = true;
            var gpx_file_slug = this.gpx_file_slug;
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
        }
        this.last_status = d.job_status_name;
        if (this.reload == true) {
            this.round += 1;
            setTimeout(this.get_status.bind(this), 500);
        }
    }
}

class UserSegmentSplit {
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
