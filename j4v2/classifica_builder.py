from j4v2.models import *
import random

def update_from_submissions(gara: Gara):
    pass

def get_valori_aggiornati(gara: Gara):
    return [random.randint(20, 30) for _ in range(gara.numero_problemi)]

def get_righe_aggiornate(gara: Gara):
    righe = [
        [0, squadra.nome, random.randint(100,999)] + [0 for problema in gara.problemi] for squadra in gara.squadre
    ]
    posizioni = sorted(range(gara.numero_squadre), key=lambda idx: righe[idx][2], reverse=True)

    for pos, i in enumerate(posizioni, start = 1):
        righe[i][0] = pos

    return righe