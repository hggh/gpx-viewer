import * as bootstrap from "bootstrap";

export default class GToastNotification {
    constructor(message, auto_hide=true, delay=1500) {
        this.message = message;
        this.auto_hide = auto_hide;
        this.delay = delay;
        this.gtnotification_base = document.getElementById("gtnotification_base");

        this.generate();
    }
    generate() {
        let toast = document.createElement("div");
        toast.classList.add("toast", "align-items-center", "text-bg-primary", "border-0");
        toast.role = "alert";
        toast.areaLive = "assertive";
        toast.areaAtomic = true;
        toast.style = "z-index:2000";
        toast.dataset.bsAutohide = this.auto_hide;
        toast.dataset.bsDelay = this.delay;

        let flex = document.createElement("div");
        flex.classList.add("d-flex");

        let toast_body = document.createElement("div");
        toast_body.classList.add("toast-body");
        toast_body.innerHTML = this.message;
        flex.appendChild(toast_body);

        let button = document.createElement("button");
        button.type = "button";
        button.classList.add("btn-close", "btn-close-white", "me-2", "m-auto");
        button.dataset.bsDismiss = "toast";
        button.ariaLabel = "Close";
        flex.appendChild(button);

        toast.appendChild(flex);
        this.gtnotification_base.appendChild(toast);

        this.b = new bootstrap.Toast(toast)
    }
    show() {
        return this.b.show();
    }
}
