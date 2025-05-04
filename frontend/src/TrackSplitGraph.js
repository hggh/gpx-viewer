import L, { DomUtil, point } from "leaflet";
import * as d3 from "d3";

export default  class TrackSplitGraph {
    constructor(gpx_file_slug, segment_pk, map, segment, track_name) {
        this.gpx_file_slug = gpx_file_slug;
        this.segment_pk = segment_pk;
        this.map = map;
        this.segment = segment;
        this.moving = false;
        this.tab_element_name = "split_track_graph";
        this.split_track_graph_legend = L.DomUtil.get("split_track_graph_legend");
        this.split_track_graph_legend_text = L.DomUtil.get("split_track_graph_legend_text");
        this.split_create_edit_button = L.DomUtil.get("track_split_edit");
        this.split_lines = [];
        this.editing = false;
        this.map_height = parseInt(document.getElementById('map').style.height.replace('px', ''));

        this.margin = {
            top: 10,
            bottom: 49,
            right: 30,
            left: 50,
        };

        this.leaflet_layer_group = L.layerGroup();
        this.leaflet_layer_group.addTo(this.map);

        this.split_create_edit_button.addEventListener("click", this.create_edit_button_click.bind(this), false);
        this.splitted_data = new Array();
    }
    create_edit_button_click(event) {
        L.DomUtil.get("right_canvas_close").click();

        if (this.editing == false) {
            DomUtil.get(this.tab_element_name).classList.remove("collapse");
            this.split_track_graph_legend.classList.remove("collapse");
            this.split_track_graph_legend_text.classList.remove("collapse");
            document.getElementById('map').style.height = (this.map_height - 300) + "px";

            this.editing = true;
            this.graph();
            this.draw_legend_text();
            this.draw_split_lines();

            this._marker = L.circleMarker([0, 0], {'color': '#0000ff'}).addTo(this.map);
            this._marker.setRadius(7);
        }
    }
    draw_tooltip(xpos, point) {
        this.xAxisLine.attr("x", xpos);

        var mouse_text_xpos = xpos + 10;
        if (xpos > (this.width / 2)) {
            mouse_text_xpos = xpos - 120;
        }

        if (this.splitted_data.length > 0 ) {
            let left_split = null;
            let left_split_key = null;
            for (let key = this.splitted_data.length -1 ; key >= 0 ; key--) {
                let currsplit = this.splitted_data[key];
                if (point.distance > currsplit.distance) {
                    left_split = currsplit;
                    left_split_key = key;
                    break;
                }
            }
            if (left_split) {
                let start_point = this.x(left_split.distance / 1000);
                this.yAxisLine.attr("y", this.height + 20);
                this.yAxisLine.attr("x", start_point);
                this.yAxisLine.attr("width", xpos - start_point);

                this.split_kilometer_text_left.text(Math.round((point.distance - left_split.distance) / 1000) + "km")
                        .style("opacity", 1)
                        .attr("y", this.height + 45)
                        .attr("x", start_point);
            }
            let next = this.splitted_data[left_split_key + 1];
            if (next) {
                this.yAxisLineRight.attr("y", this.height + 20);
                this.yAxisLineRight.attr("x", xpos);
                this.yAxisLineRight.attr("width", this.x(next.distance / 1000) - xpos);

                this.split_kilometer_text_right.text(Math.round((next.distance - point.distance) / 1000) + "km")
                        .style("opacity", 1)
                        .attr("y", this.height + 45)
                        .attr("x", this.x(next.distance / 1000) - 20);
            }
            else {
                let last_point = this.segment.points[this.segment.points.length -1];
                let end_point_xpos = this.x(last_point.distance / 1000);

                this.split_kilometer_text_right.text(Math.round((last_point.distance - point.distance) / 1000) + "km")
                        .style("opacity", 1)
                        .attr("y", this.height + 45)
                        .attr("x", end_point_xpos - 20);

                this.yAxisLineRight.attr("y", this.height + 20);
                this.yAxisLineRight.attr("x", xpos);
                this.yAxisLineRight.attr("width", end_point_xpos - xpos);
            }
        }
        if (this.splitted_data.length == 0) {
            let start_point = this.x(0);
            this.yAxisLine.attr("y", this.height + 20);
            this.yAxisLine.attr("x", start_point);
            this.yAxisLine.attr("width", xpos - start_point);

            this.split_kilometer_text_left.text(Math.round(point.distance / 1000) + " km")
                    .style("opacity", 1)
                    .attr("y", this.height + 45)
                    .attr("x", start_point);
            let last_point = this.segment.points[this.segment.points.length -1];
            let end_point_xpos = this.x(last_point.distance / 1000);

            this.split_kilometer_text_right.text(Math.round((last_point.distance - point.distance) / 1000) + "km")
                        .style("opacity", 1)
                        .attr("y", this.height + 45)
                        .attr("x", end_point_xpos - 20);

            this.yAxisLineRight.attr("y", this.height + 20);
            this.yAxisLineRight.attr("x", xpos);
            this.yAxisLineRight.attr("width", end_point_xpos - xpos);

        }

        this.mouse_text
            .text(Math.round(point.distance / 1000) + " km / " + Math.round(point.elevation) + "m (click to split) ")
            .style("opacity", 1)
            .attr("class", "mouse-text")
            .attr("y", "40")
            .attr("x", mouse_text_xpos);
    }
    draw_split_lines() {     
        d3.selectAll("g").selectChildren().each(function(p, j) {
            if (this.dataset.func && this.dataset.func == "split-line") {
                this.remove();
            }
        });

        this.split_track_graph_legend.innerHTML = "";

        this.splitted_data.keys().forEach((key) => {
            let element = this.splitted_data[key];

            let segment_end_point = null;
            let e = this.splitted_data[key + 1];
            if (e) {
                segment_end_point = this.splitted_data[key + 1];
            }
            else {
                segment_end_point = this.segment.points[this.segment.points.length -1];
            }

            let xpos = this.x(element.distance / 1000);

            let g = this.foreground.append("g")
                .attr("data-key", key)
                .attr("data-func", "split-line");
            
            this.split_lines[key] = g.append("rect")
                .attr("class", "splitxAxisLine")
                .attr("stroke-with", "1px")
                .attr("width", ".5px")
                .attr("height", this.height)
                .attr("x", xpos);

            let legend = document.createElement("div");
            let margin_top = "5px";
            if (key % 2 == 1) {
                margin_top = "10px";
            }
            legend.setAttribute("style", "position:absolute;left:"+ (xpos + this.margin.left) + "px;margin-top:"+ margin_top + ";");

            if (key != 0) {
                // Split Segment 0 is not deletable.
                let button_delete = document.createElement("button");
                button_delete.classList.add("btn", "btn-secondary",  "btn-sm");
                button_delete.title = "Delete Split";
                button_delete.dataset.key = key;
                let delete_image = document.createElement("img");
                delete_image.src = "/static/bootstrap-icons-1.11.2/trash.svg";
                delete_image.title = "Delete Split";
                delete_image.dataset.key = key;
                button_delete.appendChild(delete_image);
                legend.appendChild(button_delete);
                legend.appendChild(document.createElement("br"));

                let button_move = document.createElement("button");
                button_move.classList.add("btn", "btn-secondary",  "btn-sm")
                button_move.dataset.key = key;

                let move_image = document.createElement("img");
                move_image.src = "/static/bootstrap-icons-1.11.2/arrows-expand-vertical.svg";
                move_image.title = "Move Split";
                move_image.dataset.key = key;
                button_move.appendChild(move_image);
                legend.appendChild(button_move);

                button_move.addEventListener("click", (event) => {
                    this.yAxisLine.attr("width", 0);
                    this.yAxisLineRight.attr("width", 0);
                    this.split_kilometer_text_left.text("");
                    this.split_kilometer_text_right.text("");

                    this.moving = true;
                    this.moving_key = parseInt(event.target.dataset.key);
                    this.split_lines[this.moving_key].on("click", this.movement_click.bind(this));

                    this.mouse_text.text("").style("opacity", 0);
                    this.xAxisLine.attr("height", 0);
                });

                button_delete.addEventListener("click", (event) => {
                    this.moving = false;
                    this.moving_key = null;
                    let splitted_data = new Array();
                    this.splitted_data.keys().forEach((key) => {
                        if (key != parseInt(event.target.dataset.key)) {
                            splitted_data.push(this.splitted_data[key]);
                        }
                    });
                    if (splitted_data.length == 1) {
                        // if one segment left, we clean also the first one.
                        this.splitted_data = [];
                    }
                    else {
                        this.splitted_data = splitted_data;
                    }
                    this.draw_split_lines();
                    this.draw_gpx_track_lines_map();
                    this.draw_legend_text();
                });
            }
            this.split_track_graph_legend.appendChild(legend);
        });
    }
    async draw_legend_text() {
        this.split_track_graph_legend_text.innerHTML = "";
        this.splitted_data.keys().forEach((key) => {
            let element = this.splitted_data[key];

            let segment_end_point = null;
            let e = this.splitted_data[key + 1];
            if (e) {
                segment_end_point = this.splitted_data[key + 1];
            }
            else {
                segment_end_point = this.segment.points[this.segment.points.length -1];
            }
            let kilometer = Math.round((segment_end_point.distance - element.distance) / 1000);
            let xpos = this.x(element.distance / 1000);

            let legend = document.createElement("div");
            legend.setAttribute("style", "position:absolute;left:"+ (xpos + this.margin.left) + "px;");

            let segment_total_ascent = 0;
            let segment_total_descent = 0;
            let priv_point = null;
            this.segment.points.slice(element.point_number, segment_end_point.point_number + 1).forEach((p) => {
                let elevation_diff_to_previous = null;

                if (priv_point !== null) {
                    if (priv_point.elevation !== null && p.elevation != null) {
                        elevation_diff_to_previous = priv_point.elevation - p.elevation
                    }
                }
                priv_point = p

                if (elevation_diff_to_previous !== null) {
                    if (elevation_diff_to_previous > 0) {
                        segment_total_descent += elevation_diff_to_previous
                    }
                    else {
                        segment_total_ascent += elevation_diff_to_previous
                    }
                }
            });

            let legend_text = document.createElement("div");
            let content = "<small>" + kilometer + "km<br/>"
            content += '<img  src="/static/bootstrap-icons-1.11.2/arrow-up-right.svg" title="Up"/> ' + Math.round(Math.abs(segment_total_ascent)) + "m<br/>";
            content += '<img src="/static/bootstrap-icons-1.11.2/arrow-down-right.svg" title="Down"/> ' + Math.round(Math.abs(segment_total_descent)) + "m";
            content += "</small>";
            
            legend_text.innerHTML = content;
            legend.appendChild(legend_text);

            this.split_track_graph_legend_text.appendChild(legend);
        });

        let button_upload_div = document.createElement("div");
        button_upload_div.style = "padding-top:80px;"
        button_upload_div.classList.add("container", "text-center");
        let button_upload = document.createElement("button");
        button_upload.classList.add("btn", "btn-success");
        button_upload.type = "button";
        button_upload.innerHTML = "Save Split!";
        button_upload_div.appendChild(button_upload);
        button_upload.addEventListener("click", this.upload_data.bind(this), false);
        this.split_track_graph_legend_text.appendChild(button_upload_div);
    }
    download_data() {
        var instance = this;
        let url = "/api/gpxfile/" + this.gpx_file_slug + "/user_segment_splits/";
        let r = new XMLHttpRequest();
        r.open('POST', url);
        r.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        r.addEventListener("load", (event) => {
            instance.splitted_data = JSON.parse(r.responseText);
            instance.draw_gpx_track_lines_map();

        });
        r.send(JSON.stringify({"segment_pk": this.segment_pk}));
    }
    upload_data(event) {
        let spinner = document.createElement("div");
        spinner.classList.add("spinner-border", "text-primary");
        spinner.role = "status";
        this.split_track_graph_legend_text.appendChild(spinner);
        event.target.disabled = true;
        var url = "/api/gpxfile/" + this.gpx_file_slug + "/user_segment_split/";
        var r = new XMLHttpRequest();
        r.open('POST', url);
        r.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
        r.addEventListener("load", (event) => {
            location.reload();
        });
        r.send(JSON.stringify({"segment_pk": this.segment_pk, "splitted_data": this.splitted_data}));
    }
    draw_gpx_track_lines_map() {
        this.leaflet_layer_group.remove();
        this.leaflet_layer_group = L.layerGroup();
        this.leaflet_layer_group.addTo(this.map);

        this.splitted_data.keys().forEach((key) => {
            let element = this.splitted_data[key];
            let data = new Array();

            let track_html_color = "#66ff66";
            if (key % 2 == 0) {
                track_html_color = "#ff33cc";
            }

            let segment_end_point = null;
            let e = this.splitted_data[key + 1];
            if (e) {
                segment_end_point = this.splitted_data[key + 1];
            }
            else {
                segment_end_point = this.segment.points[this.segment.points.length -1];
            }

            this.segment.points.slice(element.point_number, segment_end_point.point_number + 1).forEach((point) => {
                data.push([point.lat, point.lon]);
            });

            let line = L.polyline(data, {'color': track_html_color, 'opacity': 0.5, 'weight': 8}).addTo(this.leaflet_layer_group);
        });
    }
    pm_mouseover(event) {
        var [xpos, ypos] = d3.pointer(event);
        var mouse_pointer_distance = this.x.invert(xpos);
        var i = d3.bisector((d) => d.distance).right(this.segment.points, (mouse_pointer_distance * 1000));

        if (this.moving == true) {
            let left = this.splitted_data[this.moving_key - 1];
            if (left) {
                let left_xpos = this.x(left.distance / 1000);
                // if we have a split left don't allow to move left of the left split. Ho? easy eh?
                if ((left_xpos + 10) > xpos) {
                    xpos = left_xpos + 10;
                    mouse_pointer_distance = this.x.invert(xpos);
                    i = d3.bisector((d) => d.distance).right(this.segment.points, (mouse_pointer_distance * 1000));
                }
            }
            let right = this.splitted_data[this.moving_key + 1];
            if (right) {
                let right_xpos = this.x(right.distance / 1000);
                // left movement only to the next right split, same as left
                if (xpos > (right_xpos - 10)) {
                    xpos = right_xpos - 10;
                    mouse_pointer_distance = this.x.invert(xpos);
                    i = d3.bisector((d) => d.distance).right(this.segment.points, (mouse_pointer_distance * 1000));
                }
            }

            this.split_lines[this.moving_key].attr("x", xpos);
            this.splitted_data[this.moving_key] = this.segment.points[i];
            this.draw_gpx_track_lines_map();
            this.draw_legend_text();   
        }
        else {
            this.xAxisLine.attr("x", xpos);
            this.xAxisLine.attr("height", this.height);
            this.draw_tooltip(xpos, this.segment.points[i]);
        }
        this._marker.setLatLng([this.segment.points[i].lat, this.segment.points[i].lon]);
    }
    movement_click(event) {      
        this.split_lines[this.moving_key].on("click", null);

        this.moving = false;
        this.moving_key = null;

        this.draw_split_lines();
        this.draw_gpx_track_lines_map();
        this.draw_legend_text();
    }
    mouse_marker_click(event) {
        var [xpos, ypos] = d3.pointer(event);
        this.xAxisLine.attr("x", xpos);
  
        var mouse_pointer_distance = this.x.invert(xpos);
        var i = d3.bisector((d) => d.distance).right(this.segment.points, (mouse_pointer_distance * 1000));

        this.splitted_data.push(this.segment.points[i]);
        if (this.splitted_data.length == 1) {
            this.splitted_data.push(this.segment.points[0]);
        }
        this.splitted_data.sort((a, b) => a.point_number - b.point_number);

        this.draw_split_lines();
        this.draw_gpx_track_lines_map();
        this.draw_legend_text();
    }
    async graph() {
        this.width = parseInt(L.DomUtil.get(this.tab_element_name).clientWidth) - this.margin.right - this.margin.left;
        this.height = 150 - this.margin.top - this.margin.bottom;

        this.svg = d3.select("#" + this.tab_element_name).append("svg")
            .attr("width", this.width + this.margin.right + this.margin.left)
            .attr("height", this.height + this.margin.top + this.margin.bottom)
            .append("g")
            .attr("transform",`translate(${this.margin.left},${this.margin.top})`);

        this.background = this.svg.append("g").attr("class", "group1");
        this.foreground = this.svg.append("g").attr("class", "group2");

        this.x = d3.scaleLinear();
        this.y = d3.scaleLinear();

        this.split_kilometer_text_right = this.foreground.append("text")
            .attr("class", "kilometer-text-right")
            .style("opacity", 0)
            .attr("text-anchor", "right");

        this.split_kilometer_text_left = this.foreground.append("text")
            .attr("class", "kilometer-text-left")
            .style("opacity", 0)
            .attr("text-anchor", "right");

        this.mouse_text = this.foreground.append("g")
            .append("text")
            .style("opacity", 0)
            .attr("text-anchor", "right");

        const listeningRect = this.foreground
            .append("rect")
            .attr("class", "listening-rect")
            .attr("width", this.width)
            .attr("height", this.height);

        this.xAxisLine = this.foreground.append("g").append("rect")
        .attr("class", "dotted")
        .attr("stroke-with", "1px")
        .attr("width", ".5px")
        .attr("height", this.height);

        this.yAxisLine = this.background.append("g").append("rect")
            .attr("stroke-with", "4px")
            .attr("class", "split-graph-line-left")
            .attr("width", "10px")
            .attr("height", "10");

        this.yAxisLineRight = this.background.append("g").append("rect")
            .attr("stroke-with", "4px")
            .attr("class", "split-graph-line-right")
            .attr("width", "10px")
            .attr("height", "10");

        listeningRect.on("mousemove", this.pm_mouseover.bind(this));
        this.xAxisLine.on("click", this.mouse_marker_click.bind(this));

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