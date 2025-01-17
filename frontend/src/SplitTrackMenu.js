export default class SplitTrackMenu {
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