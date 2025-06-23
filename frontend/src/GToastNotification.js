import * as bootstrap from "bootstrap";

export default class GToastNotification {
    constructor(header_message, message, time_message="", auto_hide=true, delay=1500) {
        this.header_message = header_message;
        this.message = message;
        this.time_message = time_message;
        this.auto_hide = auto_hide;
        this.delay = delay;
        this.gtnotification_base = document.getElementById("gtnotification_base");

        this.generate();
    }
    generate() {
        let toast = document.createElement("div");
        toast.classList.add("toast");
        toast.role = "alert";
        toast.areaLive = "assertive";
        toast.areaAtomic = true;
        toast.style = "z-index:2000";
        toast.dataset.bsAutohide = this.auto_hide;
        toast.dataset.bsDelay = this.delay;

        let toast_header = document.createElement("div");
        toast_header.classList.add("toast-header");

        let img = document.createElement("img");
        img.src = "...";
        img.alt = "...";
        img.classList.add("rounded", "me-2");
        toast_header.appendChild(img);

        let header_text = document.createElement("strong");
        header_text.classList.add("me-auto");
        header_text.innerHTML = this.header_message;
        toast_header.appendChild(header_text);

        let time = document.createElement("small");
        time.classList.add("text-body-secondary");
        time.innerHTML = this.time_message;
        toast_header.appendChild(time);

        let button = document.createElement("button");
        button.type = "button";
        button.classList.add("btn-close");
        button.dataset.bsDismiss = "toast";
        button.ariaLabel = "Close";
        toast_header.appendChild(button);

        toast.appendChild(toast_header);

        let toast_body = document.createElement("div");
        toast_body.classList.add("toast-body");
        toast_body.innerHTML = this.message;
        toast.appendChild(toast_body);

        this.gtnotification_base.appendChild(toast);

        this.b = new bootstrap.Toast(toast)
    }
    show() {
        return this.b.show();
    }
}
