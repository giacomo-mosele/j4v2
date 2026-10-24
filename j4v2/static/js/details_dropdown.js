document.querySelectorAll("details.management-dropdown, details.review-dropdown").forEach((details) => {
    const summary = details.querySelector(":scope > summary");
    const panel = details.querySelector(":scope > .dropdown-panel");

    if (!summary || !panel) {
        return;
    }

    summary.addEventListener("click", (event) => {
        event.preventDefault();

        if (details.dataset.animating) {
            return;
        }

        const isOpening = !details.open;
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        if (prefersReducedMotion || typeof panel.animate !== "function") {
            details.open = isOpening;
            return;
        }

        details.dataset.animating = "true";
        panel.style.overflow = "hidden";

        if (isOpening) {
            details.open = true;
        }

        const startHeight = isOpening ? 0 : panel.getBoundingClientRect().height;
        const endHeight = isOpening ? panel.scrollHeight : 0;
        const animation = panel.animate(
            [
                { height: `${startHeight}px`, opacity: isOpening ? 0 : 1 },
                { height: `${endHeight}px`, opacity: isOpening ? 1 : 0 }
            ],
            { duration: 220, easing: "ease" }
        );

        animation.addEventListener("finish", () => {
            if (!isOpening) {
                details.open = false;
            }
            animation.cancel();
            panel.style.overflow = "";
            delete details.dataset.animating;
        }, { once: true });
    });
});
