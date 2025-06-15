import * as d3 from "d3";
import TrackSegment from "./TrackSegment";
import Cookies from "js-cookie";


export default class GPXFileStatus {
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
        r.setRequestHeader("X-CSRFToken", Cookies.get('csrftoken'));
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
            d3.json('/api/gpxfile/' + this.gpx_file_slug + '/json').then(function (data) {
                var index = 0;
                var active_tab = true;
                data.forEach(track => {
                    track.segments.forEach(segment => {
                        new TrackSegment(this.gpx_file_slug, segment.segment_id, this.map, segment, track.name, active_tab, index);
                        active_tab = false;
                    });
                    index += 1;
                });
                if (index > 1) {
                    document.getElementById('elevation_tab_previous').classList.remove("collapse");
                    document.getElementById('elevation_tab_next').classList.remove("collapse");
                }
            }.bind(this));
        }
        this.last_status = d.job_status_name;
        if (this.reload == true) {
            this.round += 1;
            setTimeout(this.get_status.bind(this), 500);
        }
    }
}