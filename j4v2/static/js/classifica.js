const valoriRow = document.getElementById("valoriRow");
const tempoLabel = document.getElementById("tempoLabel");
const classificaTable = document.getElementById("classificaTable");
const mostraPosizioni = document.getElementById("mostraPosizioni");
let posizioniNascoste = null;
let ultimoPayload = null;

function aggiorna_classifica(payload) {
    ultimoPayload = payload;
    const oscuramento = Number(payload.oscuramento) === 1;
    classificaTable.classList.toggle("classifica-nascosta", oscuramento);
    tempoLabel.classList.toggle("tempo-oscurato", oscuramento);
    tempoLabel.textContent = payload.tempo;
    if (oscuramento) return;

    const garaTerminata = payload.tempo === "Gara terminata";
    if (garaTerminata) {
        if (payload.classifica_archiviata) {
            posizioniNascoste = 0;
        } else if (posizioniNascoste === null) {
            posizioniNascoste = payload.squadre_nascoste;
        }
    }

    const valori = payload.valori;
    const righe = payload.righe;
    const righeSquadra = Array.from({ length: numero_squadre }, (_, indice) =>
        document.getElementById(`squadraRow_${indice}`)
    );
    const posizioniIniziali = new Map(
        righeSquadra.map((riga) => [riga, riga.getBoundingClientRect().top])
    );

    // AGGIORNA VALORI
    valoriRow.innerHTML = "";
    for (let p = -3; p < numero_problemi; p++) {
        const cell = document.createElement("td");
        cell.classList.add("table__cell");
        if (p < 0) cell.innerHTML = "";
        else cell.innerHTML = valori[p];
        valoriRow.append(cell);
    }

    const righeOrdinate = righe
        .map((riga, indice) => ({ dati: riga, elemento: righeSquadra[indice] }))
        .sort((a, b) => {
            const posizioneA = a.dati[0][0];
            const posizioneB = b.dati[0][0];
            const ospiteA = typeof posizioneA === "string" && posizioneA.startsWith("G");
            const ospiteB = typeof posizioneB === "string" && posizioneB.startsWith("G");

            if (ospiteA !== ospiteB) return ospiteA ? 1 : -1;

            const numeroA = Number(ospiteA ? posizioneA.slice(1) : posizioneA);
            const numeroB = Number(ospiteB ? posizioneB.slice(1) : posizioneB);
            return numeroA - numeroB;
        });

    const righeNonOspiti = righeOrdinate.filter(({ dati }) =>
        !(typeof dati[0][0] === "string" && dati[0][0].startsWith("G"))
    );
    const righeDaNascondere = new Set(
        garaTerminata && posizioniNascoste > 0
            ? righeNonOspiti.slice(0, posizioniNascoste).map(({ elemento }) => elemento)
            : []
    );
    const righeVisualizzate = [
        ...righeOrdinate
            .filter(({ elemento }) => righeDaNascondere.has(elemento))
            .sort((a, b) => righeSquadra.indexOf(a.elemento) - righeSquadra.indexOf(b.elemento)),
        ...righeOrdinate.filter(({ elemento }) => !righeDaNascondere.has(elemento)),
    ];

    // AGGIORNA RIGHE SQUADRE
    for (let s = 0; s < numero_squadre; s++) {
        const rigaSquadra = righeSquadra[s];
        rigaSquadra.innerHTML = "";
        for (let p = 0; p < numero_problemi + 3; p++) {
            const dato = righe[s][p];
            const cell = document.createElement("td");
            cell.classList.add("table__cell");
            if (righeDaNascondere.has(rigaSquadra)) {
                cell.textContent = "?";
            } else {
                cell.textContent = dato[0];
                if (p >= 3) {
                    if (dato[1] === -1) cell.classList.add("casellina-1");
                    if (dato[1] === 1) cell.classList.add("casellina1");
                    if (dato[2] === 1) cell.classList.add("jolly");
                }
            }
            rigaSquadra.append(cell);
        }
    }

    const contenitoreRighe = righeSquadra[0]?.parentElement;
    if (!contenitoreRighe) return;

    for (const { elemento } of righeVisualizzate) {
        contenitoreRighe.append(elemento);
    }

    mostraPosizioni.hidden = !garaTerminata || posizioniNascoste <= 0;
    if (!mostraPosizioni.hidden) {
        if (posizioniNascoste === 2) {
            mostraPosizioni.textContent = "Mostra le prime due posizioni";
        } else {
            const prossimaPosizione = posizioniNascoste;
            mostraPosizioni.textContent = `Mostra la posizione ${prossimaPosizione}`;
        }
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    for (const { elemento } of righeVisualizzate) {
        const spostamentoY = posizioniIniziali.get(elemento) - elemento.getBoundingClientRect().top;
        if (Math.abs(spostamentoY) < 1) continue;

        elemento.animate(
            [
                { transform: `translateY(${spostamentoY}px)` },
                { transform: "translateY(0)" },
            ],
            {
                duration: 1800,
                easing: "cubic-bezier(0.2, 0.75, 0.25, 1)",
            }
        );
    }
}

mostraPosizioni.addEventListener("click", (event) => {
    event.preventDefault();
    if (posizioniNascoste === null || posizioniNascoste <= 0 || !ultimoPayload) return;
    posizioniNascoste = posizioniNascoste <= 2 ? 0 : posizioniNascoste - 1;
    aggiorna_classifica(ultimoPayload);
});

async function aggiornaPeriodicamente() {
    try {
        const response = await fetch(`/get_classifica_table?id=${id_gara}`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        aggiorna_classifica(await response.json());
    } catch (error) {
        console.error(error);
    } finally {
        setTimeout(aggiornaPeriodicamente, 3000);
    }
}

aggiornaPeriodicamente();
