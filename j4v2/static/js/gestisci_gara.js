document.addEventListener("DOMContentLoaded", function () {
    const modalElement = document.getElementById("submission-modal");
    const form = document.getElementById("submission-form");
    const squadraIdInput = document.getElementById("squadra-id");
    const problemaNumeroInput = document.getElementById("problema-numero");
    const selectedSquadra = document.getElementById("selected-squadra");
    const selectedProblema = document.getElementById("selected-problema");
    const risultatoInput = document.getElementById("resultato");
    const isJollyInput = document.getElementById("is-jolly");
    const modal = window.bootstrap.Modal.getOrCreateInstance(modalElement);

    document.querySelectorAll(".inserimento-cell").forEach(function (button) {
        button.addEventListener("click", function () {
            squadraIdInput.value = button.dataset.squadraId;
            problemaNumeroInput.value = button.dataset.problemaNumero;
            selectedSquadra.textContent = button.dataset.squadraNome;
            selectedProblema.textContent = "Problema " + button.dataset.problemaNumero;
            risultatoInput.value = "";
            isJollyInput.checked = false;
            risultatoInput.disabled = false;
            risultatoInput.required = true;
            modal.show();
        });
    });

    isJollyInput.addEventListener("change", function () {
        risultatoInput.disabled = isJollyInput.checked;
        risultatoInput.required = !isJollyInput.checked;
        if (isJollyInput.checked) {
            risultatoInput.value = "";
        }
    });

    form.addEventListener("submit", function () {
        const risultato = isJollyInput.checked ? 0 : Number(resultatoInput.value);
        if (!isJollyInput.checked && (!Number.isInteger(resultato) || risultato < 0 || risultato > 9999)) {
            risultatoInput.setCustomValidity("Il risultato deve essere un numero intero tra 0 e 9999.");
            risultatoInput.reportValidity();
            return;
        }
        risultatoInput.setCustomValidity("");
    });
});
