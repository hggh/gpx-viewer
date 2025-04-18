export default class GPXWayPointTypeStorage {
    constructor() {
        this.data = null;
        this.get_data();
    }
    get_url() {
        return '/api/gpxwaypointtype/'
    }
    update(r) {
        let d = JSON.parse(r);
        this.data = d;
    }
    get_data() {
        var r = new XMLHttpRequest();
        var instance = this;
        r.open('GET', this.get_url());
        r.addEventListener("load", function() {
            instance.update(this.responseText);
        });
        r.send();
    }
    store() {
        this.storage = {};
        this.data.forEach((element) => {
            let enabled = document.getElementById(element.html_id).checked;
            let around = document.getElementById(element.html_id + "_around").value;
            let around_duplicate = document.getElementById(element.html_id + "_around_duplicate").value;

            this.storage[element.html_id] = {
                "enabled": enabled,
                "around": around,
                "around_duplicate": around_duplicate,
            }
        });
        localStorage.setItem("gpxwaypointytpe_selections", JSON.stringify(this.storage));
    }
    load() {
        let data = JSON.parse(localStorage.getItem("gpxwaypointytpe_selections"));

        for (const [key, value] of Object.entries(data)) {
            let enabled = document.getElementById(key);
            if (enabled) {
                enabled.checked = value.enabled;
                document.getElementById(key + "_around").value = value.around;
                document.getElementById(key + "_around_duplicate").value = value.around_duplicate;
            }
        }
    }
    reset_defaults() {
        this.data.forEach((element) => {
            document.getElementById(element.html_id).checked = element.checked;
            document.getElementById(element.html_id + "_around").value = element.around;
            document.getElementById(element.html_id + "_around_duplicate").value = element.around_duplicate;
        });
    }
}