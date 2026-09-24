from datetime import datetime, timezone
from zoneinfo import ZoneInfo

int_to_day = {
    0: "Lunedì",
    1: "Martedì",
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì",
    5: "Sabato",
    6: "Domenica"
}

ruoli_text_dict = {
    0: "Ruolo: User",
    1: "Ruolo: Admin",
    2: "Ruolo: Developer"
}


def _clean_string(value):
    if value is None:
        return ""
    return str(value).strip()


def _parse_csv_ints(value, field_name, allow_empty = True, min_value = 0, require_descending = False):
    if value is None:
        if allow_empty:
            return []
        raise ValueError(f"'{field_name}' non può essere vuoto.")

    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(",")

    parsed = []
    for item in items:
        cleaned = _clean_string(item)
        if cleaned == "":
            if allow_empty:
                continue
            raise ValueError(f"'{field_name}' contiene un valore vuoto.")

        try:
            number = int(cleaned)
        except (TypeError, ValueError):
            raise ValueError(f"'{field_name}' deve contenere solo numeri interi separati da virgola.")

        if number < min_value:
            raise ValueError(f"'{field_name}' non può contenere valori minori di {min_value}.")

        parsed.append(number)

    if require_descending and len(parsed) > 1:
        for previous, current in zip(parsed, parsed[1:]):
            if current >= previous:
                raise ValueError(f"'{field_name}' deve essere ordinato in modo decrescente, ad esempio '15,10,5'.")

    return parsed


def italian_to_unix(italian_time: datetime) -> int: # passare come argomento un datetime con tzinfo = ZoneInfo("Europe/Rome")
    utc_time = italian_time.astimezone(ZoneInfo("UTC"))
    unix_time = int(utc_time.timestamp())
    return unix_time


def unix_to_italian(unix_time) -> datetime:
    if unix_time is None:
        return None
    output_utc = datetime.fromtimestamp(unix_time, tz = timezone.utc)
    output_ita = output_utc.astimezone(ZoneInfo("Europe/Rome"))
    return output_ita


def request_find_mistake(form):
    if form is None:
        return "Errore: form non pervenuto."

    if not hasattr(form, "titolo") or _clean_string(form.titolo.data) == "":
        return "Inserire un titolo valido per la gara."

    for field_name, label, minimum in [
        ("durata", "Durata", 1),
        ("n", "n", 0),
        ("fine_incremento", "Minuti di incremento automatico", 0),
        ("tempo_jolly", "Minuti per la scelta del jolly", 0),
        ("minuti_oscuri", "Minuti a classifica oscurata", 0),
        ("top_n_squadre_nascoste", "Squadre nascoste a fine gara", 0),
    ]:
        if getattr(form, "is_allenamento", None) is not None and form.is_allenamento.data and field_name in ["n", "fine_incremento", "top_n_squadre_nascoste"]:
            continue

        if not hasattr(form, field_name):
            return f"Inserire un valore valido per '{label}'."

        value = getattr(form, field_name).data
        if value is None:
            return f"Inserire un valore valido per '{label}'."

        try:
            number = int(value)
        except (TypeError, ValueError):
            return f"Il campo '{label}' deve essere un numero intero."

        if number < minimum:
            return f"Il campo '{label}' deve essere maggiore o uguale a {minimum}."

    if (not hasattr(form, "datetime_start") or form.datetime_start.data is None) and form.start_manuale.data is False:
        return "Inserire una data e ora di inizio valida."

    if form.start_manuale.data is False:
        dt_start = form.datetime_start.data
        if dt_start.tzinfo is None:
            dt_start = dt_start.replace(tzinfo = ZoneInfo("Europe/Rome"))
        else:
            dt_start = dt_start.astimezone(ZoneInfo("Europe/Rome"))
        now_unix = int(datetime.now(timezone.utc).timestamp())
        if italian_to_unix(dt_start) < now_unix:
            return "La data e ora di inizio della gara non può essere nel passato."

    if not hasattr(form, "problemi") or form.problemi is None:
        return "Inserire almeno un problema."

    if len(form.problemi) == 0:
        return "Inserire almeno un problema."

    for index, problema in enumerate(form.problemi, start = 1):
        if problema is None:
            return f"Il problema {index} non è valido."

        if not hasattr(problema, "risultato") or problema.risultato.data is None:
            return f"Inserire un risultato valido per il problema {index}."

        try:
            risultato = int(problema.risultato.data)
        except (TypeError, ValueError):
            return f"Il risultato del problema {index} deve essere un numero intero."

        if risultato < 0 or risultato > 9999:
            return f"Il risultato del problema {index} deve essere compreso tra 0 e 9999."

    if not hasattr(form, "squadre") or form.squadre is None:
        return "Inserire almeno una squadra."

    if len(form.squadre) == 0:
        return "Inserire almeno una squadra."

    for index, squadra in enumerate(form.squadre, start = 1):
        if squadra is None:
            return f"La squadra {index} non è valida."

        nome = getattr(squadra, "nome", None)
        if nome is None or getattr(nome, "data", None) is None or _clean_string(nome.data) == "":
            return f"Inserire un nome valido per la squadra {index}."

    for field_name, label in [("bonus_risposte_string", "Bonus velocità"), ("bonus_fullato_string", "Bonus per chi fulla")]:
        if getattr(form, "is_allenamento", None) is not None and form.is_allenamento.data:
            continue

        if not hasattr(form, field_name):
            continue

        value = getattr(form, field_name).data
        if value is None or _clean_string(value) == "":
            continue

        try:
            parsed = _parse_csv_ints(value, label, allow_empty = False, min_value = 0, require_descending = True)
        except ValueError as exc:
            return str(exc)

    for field_name, label in [("user_controllanti_string", "Utenti controllanti"), ("user_spettatori_string", "Utenti spettatori")]:
        if not hasattr(form, field_name):
            continue

        if field_name == "user_spettatori_string":
            is_private = getattr(form, "is_privata", None) is not None and form.is_privata.data
            if not is_private:
                continue

        value = getattr(form, field_name).data
        if value is None or _clean_string(value) == "":
            continue

        usernames = [username.strip() for username in str(value).split(",") if username.strip() != ""]
        if not usernames:
            continue
        for username in usernames:
            if " " in username or len(username) < 3 or len(username) > 16:
                return f"'{label}' contiene uno o più username invalidi."

    return None