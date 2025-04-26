import L from "leaflet";
import * as d3 from "d3";

export default class TrackSegment {
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
        if (track_name.length > 55) {
            track_name = track_name.substring(0, 55) + "...";
        }
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
        this.tooltip = L.tooltip({permanent: true}).setLatLng([0, 0]).addTo(this.map);
        this._marker.setRadius(7);

        this._marker.addEventListener("popupclose", (event) => {
            this._marker_movement = true;
        });

        this.graph();
        this.draw_line();
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
            this.tooltip.setLatLng(p);
            this.tooltip.setContent(" " + Math.round(p.distance / 1000) + "km");
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
        this.tooltip.setLatLng([this.segment.points[i].lat, this.segment.points[i].lon]);
        this.tooltip.setContent(" " + Math.round(this.segment.points[i].distance / 1000) + "km");

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
