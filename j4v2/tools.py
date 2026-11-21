from j4v2 import app, db
from j4v2.models import *

def help():
    print("""
--- J4V2 - TOOLS PER TERMINALE ---

dump_config(Gara) -> dumpa la configurazione della gara
dump_problemi(Gara) -> dumpa i problemi della gara (con i risultati)
dump_squadre(Gara) -> dumpa le squadre della gara (con i relativi numeri per la gara)

delay_gara(Gara, t) -> sposta la gara avanti di t secondi
reset_gara(Gara) -> cancella tutte le submission della gara e resetta i jolly
elimina_gara(Gara) -> cancella gara, submission, problemi e squadre
""")


def dump_config(gara: Gara):
    print(f"--- DUMP CONFIGURAZIONE DI {gara} ---")
    print(f"id: {gara.id}")
    print(f"Titolo: {gara.titolo}")
    print(f"Richiesta da {gara.richiedente.username}")
    print(f"Tipo: {'Allenamento' if gara.is_allenamento else 'Gara'}")
    print(f"Visibilità: {'Pubblica' if gara.is_pubblica else 'Privata'}")
    print(f"Start: {gara.unix_start} ({gara.datetime_formattato['datetime_esteso']})" if gara.unix_start else "Start manuale")
    print(f"Durata: {gara.durata} minuti")
    print(f"Numero problemi: {gara.numero_problemi}")
    print(f"Numero squadre: {gara.numero_squadre} (di cui {gara.numero_ospiti} ospiti)")
    print(f"n = {gara.n}")
    print(f"Fine incremento: {gara.fine_incremento}")
    print(f"Tempo jolly: {gara.tempo_jolly}")
    print(f"Bonus risposte: {gara.bonus_risposte}")
    print(f"Bonus fullato: {gara.bonus_fullato}")
    print(f"Minuti oscuri: {gara.minuti_oscuri}")
    print(f"Squadre nascoste a fine gara: {gara.top_n_squadre_nascoste}")

def dump_problemi(gara: Gara):
    print(f"--- DUMP PROBLEMI DI {gara} ---")
    for idx, problema in enumerate(gara.problemi):
        print(f"{idx + 1} \t {problema.titolo} ( {problema.risultato} )")

def dump_squadre(gara: Gara):
    print(f"--- DUMP SQUADRE DI {gara} ---")
    for idx, squadra in enumerate(gara.squadre):
        print(f"{idx + 1} \t {squadra.nome}")


def delay_gara(gara: Gara, tempo: int):
    gara.unix_start += tempo
    db.session.commit()

def reset_gara(gara: Gara):
    inp = input(f"ATTENZIONE! Confermi di voler resettare {gara}? (y/n)")
    if inp.lower() in ["y", "yes"]:
        Submission.query.filter_by(gara_id = gara.id).delete()
        for squadra in gara.squadre:
            squadra.jolly_id = None
        db.session.commit()
    else:
        print("Reset annullato")

def elimina_gara(gara: Gara):
    inp = input(f"ATTENZIONE! Confermi di voler eliminare {gara}? (y/n)")
    if inp.lower() in ["y", "yes"]:
        db.session.execute(
            gara_controllo.delete().where(gara_controllo.c.gara_id == gara.id)
        )
        db.session.execute(
            gara_spettatori.delete().where(gara_spettatori.c.gara_id == gara.id)
        )
        Submission.query.filter_by(gara_id = gara.id).delete()
        Squadra.query.filter_by(gara_id = gara.id).delete()
        Problema.query.filter_by(gara_id = gara.id).delete()
        db.session.delete(gara)
        db.session.commit()
    else:
        print("Eliminazione annullata")
