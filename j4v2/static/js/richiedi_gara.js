function setupDynamicList(config) {
    const list = document.getElementById(config.listId);
    if (!list) {
        return;
    }

    const addButton = document.getElementById(config.addId);
    const template = document.getElementById(config.templateId);

    function refreshNumbers() {
        const entries = list.querySelectorAll(config.entrySelector);
        const labelPrefix = typeof config.getLabelPrefix === "function" ? config.getLabelPrefix() : config.labelPrefix;
        entries.forEach((entry, index) => {
            const label = entry.querySelector(config.labelSelector);
            if (label) {
                label.textContent = `${labelPrefix} ${index + 1}`;
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
    const form = document.getElementById("request-form");
    const errorMessage = form ? form.dataset.errorMessage : "";
    if (errorMessage) {
        alert(errorMessage);
    }

    const allenamentoCheck = document.getElementById("allenamentoCheck");
    const startManualeCheck = document.getElementById("startManualeCheck");
    const datetimeStartField = document.getElementById("datetime_start");
    const isPrivataCheck = document.getElementById("isPrivataBtn");
    const privateUsersFields = document.getElementById("private-users-fields");
    const submitButton = document.getElementById("submit-request-form");
    const confirmSubmitButton = document.getElementById("confirm-submit-btn");
    const confirmSubmitModal = document.getElementById("confirmSubmitModal");
    const pageTitleLegend = document.getElementById("page-title-legend");
    const nField = document.getElementById("n");
    const fineIncrementoField = document.getElementById("fine_incremento");
    const topNField = document.getElementById("top_n_squadre_nascoste");
    const bonusRisposteField = document.getElementById("bonus_risposte_string");
    const bonusFullatoField = document.getElementById("bonus_fullato_string");

    function toggleDatetimeStartState() {
        if (!startManualeCheck || !datetimeStartField) {
            return;
        }

        const isManual = startManualeCheck.checked;
        datetimeStartField.disabled = isManual;
        datetimeStartField.required = !isManual;
        datetimeStartField.setAttribute("aria-disabled", String(isManual));
    }

    function togglePrivateUsersFields() {
        if (!isPrivataCheck || !privateUsersFields) {
            return;
        }

        privateUsersFields.classList.toggle("d-none", !isPrivataCheck.checked);
    }

    function toggleAllenamentoState() {
        const isAllenamento = !!(allenamentoCheck && allenamentoCheck.checked);

        const formLabels = {
            titolo: "Titolo dell'allenamento",
            datetime_start: "Data e ora di inizio dell'allenamento",
            top_n_squadre_nascoste: "Numero di squadre nascoste a fine allenamento",
            user_controllanti_string: "Username degli utenti non admin che (oltre a te) controlleranno l'allenamento (separati da virgola)",
            is_privata: "Allenamento privato",
            user_spettatori_string: "Username degli utenti non admin che (oltre a te e a coloro specificati sopra) potranno vedere l'allenamento (separati da virgola)"
        };

        Object.entries(formLabels).forEach(([fieldId, labelText]) => {
            const field = document.getElementById(fieldId);
            if (field && field.labels && field.labels.length) {
                const baseValue = isAllenamento ? labelText : labelText.replace("dell'allenamento", "della gara").replace("l'allenamento", "la gara").replace("Numero di squadre nascoste a fine allenamento", "Numero di squadre nascoste a fine gara").replace("Allenamento privato", "Gara privata");
                field.labels[0].textContent = baseValue;
            }
        });

        if (nField) {
            nField.disabled = isAllenamento;
            nField.required = !isAllenamento;
            nField.value = isAllenamento ? "0" : nField.value;
        }

        if (fineIncrementoField) {
            fineIncrementoField.disabled = isAllenamento;
            fineIncrementoField.required = !isAllenamento;
            fineIncrementoField.value = isAllenamento ? "0" : fineIncrementoField.value;
        }

        if (topNField) {
            topNField.disabled = isAllenamento;
            topNField.required = !isAllenamento;
            topNField.value = isAllenamento ? "0" : topNField.value;
        }

        if (bonusRisposteField) {
            bonusRisposteField.disabled = isAllenamento;
            bonusRisposteField.value = isAllenamento ? "" : bonusRisposteField.value;
        }

        if (bonusFullatoField) {
            bonusFullatoField.disabled = isAllenamento;
            bonusFullatoField.value = isAllenamento ? "" : bonusFullatoField.value;
        }

        if (pageTitleLegend) {
            pageTitleLegend.textContent = isAllenamento ? "Richiedi un allenamento" : "Richiedi una gara";
            if (pageTitleLegend.dataset.userRole === "admin") {
                pageTitleLegend.textContent = isAllenamento ? "Fissa un allenamento" : "Fissa una gara";
            }
        }

        const submitActionText = isAllenamento
            ? (pageTitleLegend && pageTitleLegend.dataset.userRole === "admin" ? "Fissa l'allenamento" : "Richiedi l'allenamento")
            : (pageTitleLegend && pageTitleLegend.dataset.userRole === "admin" ? "Fissa la gara" : "Richiedi la gara");

        if (submitButton) {
            submitButton.value = submitActionText;
            submitButton.textContent = submitActionText;
        }

        const confirmMessage = document.querySelector("#confirmSubmitModal .modal-body p");
        if (confirmMessage) {
            const actionPhrase = pageTitleLegend && pageTitleLegend.dataset.userRole === "admin" ? "creazione" : "richiesta di creazione";
            confirmMessage.textContent = `Confermi la ${actionPhrase} ${isAllenamento ? "dell'allenamento" : "della gara"}?`;
        }

        const modalTitle = document.getElementById("squadreModalLabel");
        const teamLabel = isAllenamento ? "Partecipante" : "Squadra";
        const teamButtonText = isAllenamento ? "Gestisci partecipanti" : "Gestisci squadre";
        const teamModalText = isAllenamento ? "Partecipanti" : "Squadre";
        const teamAddButton = document.getElementById("add-squadra");

        if (modalTitle) {
            modalTitle.textContent = teamModalText;
        }

        const actionButton = document.querySelector('[data-bs-target="#squadreModal"]');
        if (actionButton) {
            actionButton.textContent = teamButtonText;
        }

        if (teamAddButton) {
            teamAddButton.textContent = isAllenamento ? "Aggiungi partecipante" : "Aggiungi squadra";
        }

        document.querySelectorAll(".team-entry .team-number").forEach((entry, index) => {
            entry.textContent = `${teamLabel} ${index + 1}`;
        });

        document.querySelectorAll(".team-entry label.form-control-label[for$='-nome']").forEach((label) => {
            label.textContent = `Nome ${teamLabel}`;
        });

        const teamTemplate = document.getElementById("squadra-template");
        if (teamTemplate) {
            const updatedTeamTemplate = teamTemplate.innerHTML
                .replace(/Partecipante/g, teamLabel)
                .replace(/Squadra/g, teamLabel)
                .replace(/Nome partecipante/g, `Nome ${teamLabel}`)
                .replace(/Nome squadra/g, `Nome ${teamLabel}`)
                .replace(/Aggiungi partecipante/g, `Aggiungi ${teamLabel}`)
                .replace(/Aggiungi squadra/g, `Aggiungi ${teamLabel}`)
                .replace(/Gestisci partecipanti/g, teamButtonText)
                .replace(/Gestisci squadre/g, teamButtonText);

            teamTemplate.innerHTML = updatedTeamTemplate;
        }
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
            const form = document.getElementById("request-form");
            if (form) {
                form.requestSubmit();
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

    if (allenamentoCheck) {
        pageTitleLegend.dataset.userRole = document.body.dataset.userRole || "user";
        allenamentoCheck.addEventListener("change", toggleAllenamentoState);
        toggleAllenamentoState();
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
        labelPrefix: "Squadra",
        getLabelPrefix: function () {
            return document.getElementById("allenamentoCheck")?.checked ? "Partecipante" : "Squadra";
        }
    });
});