const valoriRow = document.getElementById("valoriRow");
const tempoLabel = document.getElementById("tempoLabel");

function aggiorna_classifica(payload) {
    const valori = payload.valori;
    const righe = payload.righe;
    const tempo = payload.tempo;
    const righeSquadra = Array.from({ length: numero_squadre }, (_, indice) =>
        document.getElementById(`squadraRow_${indice}`)
    );
    const posizioniIniziali = new Map(
        righeSquadra.map((riga) => [riga, riga.getBoundingClientRect().top])
    );

    // AGGIORNA TEMPO
    tempoLabel.innerHTML = tempo;

    // AGGIORNA VALORI
    valoriRow.innerHTML = "";
    for (let p = -3; p < numero_problemi; p++) {
        const cell = document.createElement("td");
        cell.classList.add("table__cell");
        if (p < 0) cell.innerHTML = "";
        else cell.innerHTML = valori[p];
        valoriRow.append(cell);
    }

    // AGGIORNA RIGHE SQUADRE
    for (let s = 0; s < numero_squadre; s++) {
        const rigaSquadra = righeSquadra[s];
        rigaSquadra.innerHTML = "";
        for (let p = 0; p < numero_problemi + 3; p++) {
            const dato = righe[s][p];
            const cell = document.createElement("td");
            cell.classList.add("table__cell");
            cell.textContent = dato[0];
            if (p >= 3) {
                if (dato[1] === -1) cell.classList.add("casellina-1");
                if (dato[1] === 1) cell.classList.add("casellina1");
                if (dato[2] === 1) cell.classList.add("jolly");
            }
            rigaSquadra.append(cell);
        }
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
    const contenitoreRighe = righeSquadra[0]?.parentElement;
    if (!contenitoreRighe) return;

    for (const { elemento } of righeOrdinate) {
        contenitoreRighe.append(elemento);
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    for (const { elemento } of righeOrdinate) {
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
