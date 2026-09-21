function setupDynamicList(config) {
    const list = document.getElementById(config.listId);
    if (!list) {
        return;
    }

    const addButton = document.getElementById(config.addId);
    const template = document.getElementById(config.templateId);

    function refreshNumbers() {
        const entries = list.querySelectorAll(config.entrySelector);
        entries.forEach((entry, index) => {
            const label = entry.querySelector(config.labelSelector);
            if (label) {
                label.textContent = `${config.labelPrefix} ${index + 1}`;
            }

            const removeButton = entry.querySelector(config.removeSelector);
            if (removeButton) {
                removeButton.disabled = entries.length <= 1;
            }
        });
    }

    if (addButton) {
        addButton.addEventListener("click", function () {
            const index = list.querySelectorAll(config.entrySelector).length;
            const html = template.innerHTML.replace(/__INDEX__/g, String(index));
            list.insertAdjacentHTML("beforeend", html);
            refreshNumbers();
        });
    }

    list.addEventListener("click", function (event) {
        const deleteButton = event.target.closest(config.removeSelector);
        if (!deleteButton) {
            return;
        }

        const entries = list.querySelectorAll(config.entrySelector);
        if (entries.length <= 1) {
            return;
        }

        const entry = deleteButton.closest(config.entrySelector);
        if (entry) {
            entry.remove();
            refreshNumbers();
        }
    });

    refreshNumbers();
}

document.addEventListener("DOMContentLoaded", function () {
    const startManualeCheck = document.getElementById("startManualeCheck");
    const datetimeStartField = document.getElementById("datetime_start");
    const isPrivataCheck = document.getElementById("isPrivataBtn");
    const privateUsersFields = document.getElementById("private-users-fields");
    const submitButton = document.getElementById("submit-request-form");
    const confirmSubmitButton = document.getElementById("confirm-submit-btn");
    const confirmSubmitModal = document.getElementById("confirmSubmitModal");

    function toggleDatetimeStartState() {
        if (!startManualeCheck || !datetimeStartField) {
            return;
        }

        const isManual = startManualeCheck.checked;
        datetimeStartField.disabled = isManual;
        datetimeStartField.setAttribute("aria-disabled", String(isManual));
    }

    function togglePrivateUsersFields() {
        if (!isPrivataCheck || !privateUsersFields) {
            return;
        }

        privateUsersFields.classList.toggle("d-none", !isPrivataCheck.checked);
    }

    if (submitButton && confirmSubmitModal) {
        submitButton.addEventListener("click", function (event) {
            event.preventDefault();
            const modal = new bootstrap.Modal(confirmSubmitModal);
            modal.show();
        });
    }

    if (confirmSubmitButton) {
        confirmSubmitButton.addEventListener("click", function () {
            const form = document.querySelector("form");
            if (form) {
                form.submit();
            }
        });
    }

    if (startManualeCheck && datetimeStartField) {
        startManualeCheck.addEventListener("change", toggleDatetimeStartState);
        toggleDatetimeStartState();
    }

    if (isPrivataCheck && privateUsersFields) {
        isPrivataCheck.addEventListener("change", togglePrivateUsersFields);
        togglePrivateUsersFields();
    }

    setupDynamicList({
        listId: "problemi-list",
        addId: "add-problema",
        templateId: "problema-template",
        entrySelector: ".problem-entry",
        labelSelector: ".problem-number",
        removeSelector: ".remove-problema",
        labelPrefix: "Problema"
    });

    setupDynamicList({
        listId: "squadre-list",
        addId: "add-squadra",
        templateId: "squadra-template",
        entrySelector: ".team-entry",
        labelSelector: ".team-number",
        removeSelector: ".remove-squadra",
        labelPrefix: "Squadra"
    });
});