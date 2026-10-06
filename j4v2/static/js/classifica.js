const valoriRow = document.getElementById("valoriRow");

function aggiorna_classifica(payload) {
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
        else cell.innerHTML = valori[p]; // TODO: mettere il valore anziché 20
        valoriRow.append(cell);
    }

    // AGGIORNA RIGHE SQUADRE
    for (let s = 0; s < numero_squadre; s++) {
        const rigaSquadra = righeSquadra[s];
        rigaSquadra.innerHTML = "";
        for (let p = 0; p < numero_problemi + 3; p++) {
            const cell = document.createElement("td");
            cell.classList.add("table__cell");
            cell.innerHTML = righe[s][p];
            rigaSquadra.append(cell);
        }
    }

    const righeOrdinate = righe
        .map((riga, indice) => ({ dati: riga, elemento: righeSquadra[indice] }))
        .sort((a, b) => Number(a.dati[0]) - Number(b.dati[0]));
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
        setTimeout(aggiornaPeriodicamente, 5000);
    }
}

aggiornaPeriodicamente();
