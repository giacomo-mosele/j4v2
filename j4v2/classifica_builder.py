from j4v2.models import *

def update_from_submissions(gara: Gara):
    unix_now = int(datetime.now(timezone.utc).timestamp())
    minuti_passati = max((unix_now - gara.unix_start) // 60, 0)
    minuti_incrementanti = min(minuti_passati, gara.fine_incremento)

    for problema in gara.problemi:
        incremento = minuti_incrementanti

        query_submissions_corrette = Submission.query.filter_by(
            is_enabled = True,
            gara_id = gara.id,
            problema_id = problema.id,
            is_scelta_jolly = False,
            is_corretta = True
        ).order_by(Submission.unix_time, Submission.id).all()

        squadre_viste = set()
        submissions_corrette = []
        for sub in query_submissions_corrette:
            if sub.squadra_id not in squadre_viste: # fix anti ferraris
                squadre_viste.add(sub.squadra_id)
                submissions_corrette.append(sub)

        timestamp_n_esima = gara.unix_start + gara.durata * 60 # per far funzionare l'incremento per errori

        if len(submissions_corrette) >= gara.n: # problema cappato
            submission_n_esima = submissions_corrette[gara.n - 1]
            timestamp_n_esima = submission_n_esima.unix_time
            minuto_n_esima = (timestamp_n_esima - gara.unix_start) // 60

            incremento = min(incremento, minuto_n_esima)
        
        numero_sub_errate_distinte = (
            Submission.query
            .with_entities(Submission.squadra_id)
            .filter(
                Submission.is_enabled == True,
                Submission.gara_id == gara.id,
                Submission.problema_id == problema.id,
                Submission.is_scelta_jolly == False,
                Submission.is_corretta == False,
                Submission.unix_time <= timestamp_n_esima
            )
            .distinct() # fix anti noceti
            .count()
        )

        incremento += 2 * numero_sub_errate_distinte

        problema.VALORE = 20 + incremento
    
    db.session.commit()

def get_valori_aggiornati(gara: Gara):
    return [problema.VALORE for problema in gara.problemi]


def get_righe_aggiornate(gara: Gara):
    def RIGA(squadra: Squadra):
        out = [-1, squadra.nome, -1] + [0 for problema in gara.problemi]
        out[2] = gara.numero_problemi*10 + sum(out[3:]) + squadra.bonus_full + squadra.bonus_punti
        return out
    
    righe = [ RIGA(squadra) for squadra in gara.squadre ]
    posizioni = sorted(range(gara.numero_squadre), key=lambda idx: righe[idx][2], reverse=True)

    for pos, i in enumerate(posizioni, start = 1):
        righe[i][0] = pos

    return righe