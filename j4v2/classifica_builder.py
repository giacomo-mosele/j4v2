from j4v2.models import *
from collections import defaultdict
from itertools import groupby
from sqlalchemy import or_

def update_from_submissions(gara: Gara):
    def gestisci_jolly():
        squadre_senza_jolly = Squadra.query.filter_by(
            gara_id = gara.id,
            jolly_id = None
        ).all()

        id_primo_problema = gara.problemi[0].id

        for squadra in squadre_senza_jolly:
            squadra.jolly_id = id_primo_problema

            stato_jolly = 1
            submissions_precedenti_giuste_sul_primo = Submission.query.filter(
                Submission.is_enabled == True,
                Submission.gara_id == gara.id,
                or_(
                    Submission.squadra_id == squadra.id,
                    Submission.gara.has(is_allenamento = True)
                ),
                Submission.problema_id == id_primo_problema,
                Submission.is_corretta == True
            ).all()
            if submissions_precedenti_giuste_sul_primo:
                stato_jolly = -1

            new_sub = Submission(
                gara_id = gara.id,
                squadra_id = squadra.id,
                problema_id = id_primo_problema,
                unix_time = gara.unix_start + gara.tempo_jolly * 60,
                risultato = 0,
                is_corretta = False,
                stato_jolly = stato_jolly,
                is_scelta_jolly = True,
                is_enabled = True
            )
            db.session.add(new_sub)

            db.session.commit()

    unix_now = int(datetime.now(timezone.utc).timestamp())
    minuti_passati = max((unix_now - gara.unix_start) // 60, 0)
    if minuti_passati >= gara.tempo_jolly:
        gestisci_jolly()
    minuti_incrementanti = min(minuti_passati, gara.fine_incremento, gara.durata) if not gara.is_allenamento else 0

    fullante = {squadra.id: True for squadra in gara.squadre}
    latest_corretta = {squadra.id: 0 for squadra in gara.squadre} # j4v2 il primo gennaio 1970 era LIT

    for problema in gara.problemi:
        incremento = minuti_incrementanti

        query_submissions_corrette = Submission.query.filter(
            Submission.is_enabled == True,
            Submission.gara_id == gara.id,
            Submission.problema_id == problema.id,
            Submission.is_scelta_jolly == False,
            Submission.is_corretta == True
        ).order_by(Submission.unix_time, Submission.id).all()

        risolto_questo = {squadra.id: False for squadra in gara.squadre}
        squadre_viste = set()
        submissions_corrette_non_ospiti = []
        for sub in query_submissions_corrette:
            if sub.squadra_id not in squadre_viste: # fix anti ferraris
                risolto_questo[sub.squadra_id] = True
                latest_corretta[sub.squadra_id] = max(latest_corretta[sub.squadra_id], sub.unix_time)

                squadre_viste.add(sub.squadra_id)
                if not sub.squadra.is_ospite:
                    submissions_corrette_non_ospiti.append(sub)

        for squadra in gara.squadre:
            if not risolto_questo[squadra.id]:
                fullante[squadra.id] = False

        timestamp_n_esima = gara.unix_start + gara.durata * 60 # upper bound, per far funzionare l'incremento per errori

        if not gara.is_allenamento and len(submissions_corrette_non_ospiti) >= gara.n: # problema cappato
            submission_n_esima = submissions_corrette_non_ospiti[gara.n - 1]
            timestamp_n_esima = submission_n_esima.unix_time
            minuto_n_esima = (timestamp_n_esima - gara.unix_start) // 60

            incremento = min(incremento, minuto_n_esima)
        
        numero_sub_errate_distinte_non_ospiti = (
            Submission.query
            .with_entities(Submission.squadra_id)
            .filter(
                Submission.is_enabled == True,
                Submission.gara_id == gara.id,
                Submission.problema_id == problema.id,
                Submission.is_scelta_jolly == False,
                Submission.is_corretta == False,
                Submission.unix_time <= timestamp_n_esima,
                Submission.squadra.has(is_ospite=False)
            )
            .distinct() # fix anti noceti
            .count()
        )

        incremento += 2 * numero_sub_errate_distinte_non_ospiti

        problema.VALORE = 20 + incremento if not gara.is_allenamento else 20

    for squadra in gara.squadre:
        squadra.ha_fullato = fullante[squadra.id]
        squadra.unix_time_full = latest_corretta[squadra.id] if fullante[squadra.id] else None
    
    db.session.commit()

def get_valori_aggiornati(gara: Gara):
    return [problema.VALORE for problema in gara.problemi]


def get_righe_aggiornate(gara: Gara):
    ospitezza = { squadra.id: squadra.is_ospite for squadra in gara.squadre } # top 1 definizioni del belino

    squadre_non_ospiti_fullanti = (
        Squadra.query.filter(
            Squadra.gara_id == gara.id,
            Squadra.ha_fullato == True,
            Squadra.is_ospite == False
        )
    )

    soluzioni_giuste = (
        Submission.query
        .with_entities(
            Submission.id,
            Submission.problema_id,
            Submission.squadra_id,
            Submission.unix_time
        )
        .filter(
            Submission.is_enabled == True,
            Submission.gara_id == gara.id,
            Submission.is_corretta == True,
            Submission.is_scelta_jolly == False
        )
        .order_by(
            Submission.problema_id,
            Submission.unix_time,
            Submission.id
        )
        .all()
    )

    squadre_risolventi = defaultdict(set)
    numero_precedenti_non_ospiti = {}

    for sub in soluzioni_giuste:
        squadre_sul_problema = squadre_risolventi[sub.problema_id]
        if sub.squadra_id not in squadre_sul_problema:
            numero_precedenti_non_ospiti[(sub.problema_id, sub.squadra_id)] = len(squadre_sul_problema)
            if not ospitezza[sub.squadra_id]:
                squadre_sul_problema.add(sub.squadra_id)


    def RIGA(squadra: Squadra):
        subs_squadra = squadra.submissions
        subs_per_problema = {problema.id: [] for problema in gara.problemi}
        for sub in subs_squadra:
            if sub.is_enabled:
                subs_per_problema[sub.problema_id].append(sub)

        celle = {problema.id: (0,0,0) for problema in gara.problemi}
        for problema in gara.problemi:
            punteggio = 0
            colore = 0
            stato_jolly = 0
            gia_corretta = False
            for sub in subs_per_problema[problema.id]:
                mult = 2 if stato_jolly == 1 else 1
                if sub.is_scelta_jolly:
                    stato_jolly = sub.stato_jolly
                elif not sub.is_corretta:
                    punteggio -= 10 * mult
                    if not gia_corretta:
                        colore = -1
                elif not gia_corretta:
                    bonus = 0
                    numero_squadre_precedenti = numero_precedenti_non_ospiti.get(
                        (problema.id, squadra.id),
                        0
                    )
                    if numero_squadre_precedenti < gara.numero_bonus_risposte:
                        bonus = gara.bonus_risposte[numero_squadre_precedenti]
                    punteggio += (problema.VALORE + bonus) * mult
                    gia_corretta = True
                    colore = 1
            
            celle[problema.id] = (punteggio, colore, abs(stato_jolly))

        bonus_full = 0
        if squadra.ha_fullato:
            fullanti_prima = [s for s in squadre_non_ospiti_fullanti if s.unix_time_full < squadra.unix_time_full]
            numero_fullanti_prima = len(fullanti_prima)
            if numero_fullanti_prima < gara.numero_bonus_fullato:
                bonus_full = gara.bonus_fullato[numero_fullanti_prima]

        out = [(-1,0,0), (squadra.nome,0,0), (-1,0,0)] + [celle[problema.id] for problema in gara.problemi]
        if gara.is_allenamento:
            out[0] = ("/", 0, 0)
        punteggio_totale = gara.numero_problemi*10 + sum([cella[0] for cella in out[3:]]) + bonus_full + squadra.bonus_punti if not gara.is_allenamento else "/"
        out[2] = (punteggio_totale,0,0)
        return out
    
    righe_non_ospiti = [ RIGA(squadra) for squadra in gara.squadre if not squadra.is_ospite ]
    if not gara.is_allenamento:
        posizioni_non_ospiti = sorted(range(gara.numero_squadre - gara.numero_ospiti), key=lambda idx: righe_non_ospiti[idx][2], reverse=True)
        for pos, i in enumerate(posizioni_non_ospiti, start = 1):
            righe_non_ospiti[i][0] = (pos, 0, 0)
        
    righe_ospiti = [ RIGA(squadra) for squadra in gara.squadre if squadra.is_ospite ]
    if not gara.is_allenamento:
        posizioni_ospiti = sorted(range(gara.numero_ospiti), key=lambda idx: righe_ospiti[idx][2], reverse=True)
        for pos, i in enumerate(posizioni_ospiti, start = 1):
            righe_ospiti[i][0] = (f"G{pos}", 0, 0)
            righe_ospiti[i][1] = (righe_ospiti[i][1][0] + " (Ospite)", 0, 0)

    return righe_non_ospiti + righe_ospiti
