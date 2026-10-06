from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, abort, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from j4v2 import app, db, bcrypt
from j4v2.models import *
from j4v2.forms import LoginForm, RegistrationForm, RequestForm
from j4v2.utils import *
from j4v2.classifica_builder import *
from sqlalchemy import or_

import random
import string

@app.before_request
def aggiorna_database_preprocessor():
    now_unix = int(datetime.now(timezone.utc).timestamp())
    gare_da_attualizzare = Gara.query.filter(Gara.unix_start != None, Gara.unix_start <= now_unix, Gara.stato == 1).all()
    if gare_da_attualizzare:
        for gara in gare_da_attualizzare:
            gara.stato = 2
        db.session.commit()

@app.before_request
def enforce_ban():
    if current_user.is_authenticated and current_user.ruolo == -1: # questo non dovrebbe mai accadere in teoria
        logout_user()
        flash("Accesso all'accout negato: la richiesta di creazione del tuo account deve prima essere approvata da un admin", "danger")
        return redirect(url_for("index"))

    if current_user.is_authenticated and current_user.ruolo == -2:
        logout_user()
        flash("Accesso all'account negato: sei stato bannato da Jeiquarta. Se pensi che sia un errore, contatta un admin", "danger")
        return redirect(url_for("index"))

@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", title = "Richiesta non valida", error = 400, descrizione = "La richiesta inviata al server non è valida.", meme_filename = get_meme_filename()), 400
@app.errorhandler(401)
def unauthorized(e):
    return render_template("error.html", title = "Non autorizzato", error = 401, descrizione = "Devi effettuare il login per accedere a questa pagina.", meme_filename = get_meme_filename()), 401
@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", title = "Accesso negato", error = 403, descrizione = "Non hai i permessi necessari per accedere a questa pagina.", meme_filename = get_meme_filename()), 403
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", title = "Pagina non trovata", error = 404, descrizione = "La pagina che stai cercando non esiste.", meme_filename = get_meme_filename()), 404


@app.route("/")
def index():
    return redirect(url_for("calendario"))

@app.route("/calendario")
def calendario():
    now_unix = int(datetime.now(timezone.utc).timestamp())

    gare_in_corso = Gara.query.filter(
        Gara.stato == 2,
        Gara.unix_start != None, # teoricamente ridondante
        or_(
            Gara.is_pubblica == True,
            current_user.is_authenticated and current_user.ruolo >= 1,
            current_user.is_authenticated and current_user == Gara.richiedente, # teoricamente ridondante
            current_user.is_authenticated and Gara.user_spettatori.any(User.id == current_user.id)
        )
    ).all()
    gare_in_corso.sort(key = lambda g: g.unix_start)

    gare_prossime = Gara.query.filter(
        Gara.stato == 1,
        Gara.unix_start != None,
        Gara.unix_start - now_unix <= 86400,
        or_(
            Gara.is_pubblica == True,
            current_user.is_authenticated and current_user.ruolo >= 1,
            current_user.is_authenticated and current_user == Gara.richiedente, # teoricamente ridondante
            current_user.is_authenticated and Gara.user_spettatori.any(User.id == current_user.id)
        )
    ).all()
    gare_prossime.sort(key = lambda g: g.unix_start)
    
    gare_da_startare = Gara.query.filter(
        Gara.stato == 1,
        Gara.unix_start == None,
        Gara.start_manuale == True,
        or_(
            Gara.is_pubblica == True,
            current_user.is_authenticated and current_user.ruolo >= 1,
            current_user.is_authenticated and current_user == Gara.richiedente, # teoricamente ridondante
            current_user.is_authenticated and Gara.user_spettatori.any(User.id == current_user.id)
        )
    ).all()
    
    gare_lontane = Gara.query.filter(
        Gara.stato == 1,
        Gara.unix_start != None,
        Gara.unix_start - now_unix > 86400,
        or_(
            Gara.is_pubblica == True,
            current_user.is_authenticated and current_user.ruolo >= 1,
            current_user.is_authenticated and current_user == Gara.richiedente, # teoricamente ridondante
            current_user.is_authenticated and Gara.user_spettatori.any(User.id == current_user.id)
        )
    ).all()
    gare_lontane.sort(key = lambda g: g.unix_start)

    return render_template("calendario.html", title = "Calendario", gare_in_corso = gare_in_corso, gare_prossime = gare_prossime, gare_future = gare_lontane + gare_da_startare)

@app.route("/archivio_gare")
def archivio_gare():
    gare_terminate = Gara.query.filter(
        Gara.stato == 3,
        or_(
            Gara.is_pubblica == True,
            current_user.is_authenticated and current_user.ruolo >= 1,
            current_user.is_authenticated and current_user == Gara.richiedente, # teoricamente ridondante
            current_user.is_authenticated and Gara.user_spettatori.any(User.id == current_user.id)
        )
    ).all()
    gare_terminate.sort(key = lambda g: g.unix_start, reverse = True)
    return render_template("archivio_gare.html", title = "Archivio gare", gare_terminate = gare_terminate)

@app.route("/visualizza_gara")
def visualizza_gara():
    id = request.args.get("id")
    gara = Gara.query.get(id)
    if not gara:
        abort(404)
    if not gara.is_pubblica:
        if not current_user.is_authenticated:
            abort(401)
        if current_user.ruolo < 1 and current_user not in gara.user_spettatori and current_user != gara.richiedente:
            abort(403)
    
    return render_template("visualizza_gara.html", title = f"Preview: {gara.titolo}", gara = gara)


@app.route("/classifica")
def classifica():
    id = request.args.get("id")
    gara = Gara.query.get(id)
    if not gara:
        abort(404)
    if not gara.is_pubblica:
        if not current_user.is_authenticated:
            abort(401)
        if current_user.ruolo < 1 and current_user not in gara.user_spettatori and current_user != gara.richiedente:
            abort(403)

    return render_template("classifica.html", title = gara.titolo, gara = gara.basic_dict())

@app.route("/get_classifica_table")
def get_classifica_table():
    id = request.args.get("id")
    gara = Gara.query.get(id)
    if not gara:
        abort(404)
    if not gara.is_pubblica:
        if not current_user.is_authenticated:
            abort(401)
        if current_user.ruolo < 1 and current_user not in gara.user_spettatori and current_user != gara.richiedente:
            abort(403)

    update_from_submissions(gara)
    
    valori_aggiornati = get_valori_aggiornati(gara)
    righe_aggiornate = get_righe_aggiornate(gara)

    return jsonify({
        "valori": valori_aggiornati,
        "righe": righe_aggiornate
    })


@app.route("/inserimento")
def inserimento():
    id = request.args.get("id")
    gara = Gara.query.get(id)
    if not gara:
        abort(404)
    if not current_user.is_authenticated:
        abort(401)
    if current_user.ruolo < 1 and current_user not in gara.user_controllanti and current_user != gara.richiedente:
        abort(403)

    return render_template("inserimento.html", title = "Inserimento", gara = gara.basic_dict(), squadre = gara.squadre, problemi = gara.problemi)


@app.route("/inserimento/submission", methods = ["POST"])
def inserimento_submission():
    id_gara = request.form.get("gara_id")
    id_squadra = request.form.get("squadra_id")
    numero_problema = request.form.get("problema_numero")
    is_jolly = request.form.get("is_jolly") == "on"

    try:
        id_gara = int(id_gara)
        id_squadra = int(id_squadra)
        numero_problema = int(numero_problema)
    except (TypeError, ValueError):
        abort(400)

    gara = Gara.query.get(id_gara)
    squadra = Squadra.query.get(id_squadra)
    if not gara or not squadra or squadra.gara_id != id_gara:
        abort(400)
    if not current_user.is_authenticated:
        abort(401)
    if current_user.ruolo < 1 and current_user not in gara.user_controllanti and current_user != gara.richiedente:
        abort(403)
    if numero_problema < 1 or numero_problema > gara.numero_problemi:
        abort(400)

    problema = gara.problemi[numero_problema - 1]
    risultato = request.form.get("risultato")
    if is_jolly:
        risultato = 0
    else:
        try:
            risultato = int(risultato)
        except (TypeError, ValueError):
            abort(400)
        if risultato < 0 or risultato > 9999:
            abort(400)

    submissions_precedenti_giuste = Submission.query.filter_by(gara_id = id_gara, squadra_id = id_squadra, problema_id = problema.id, is_corretta = True).all()
    stato_jolly = 0
    if is_jolly:
        if squadra.jolly_id is not None:
            flash("Errore: la squadra ha già piazzato un jolly in precedenza", "danger")
            return redirect(url_for("inserimento", id = id_gara))
        if submissions_precedenti_giuste:
            stato_jolly = -1 # il jolly è piazzato dopo una submission corretta
        else:
            stato_jolly = 1
            squadra.jolly_id = problema.id

    new_submission = Submission(
        gara_id = id_gara,
        squadra_id = id_squadra,
        problema_id = problema.id,
        unix_time = int(datetime.now(timezone.utc).timestamp()),
        risultato = risultato,
        is_corretta = (risultato == problema.risultato),
        bonus_associato = 0, # viene calcolato in update_from_submissions()
        stato_jolly = stato_jolly,
        is_scelta_jolly = is_jolly,
        is_enabled = True,
    )
    db.session.add(new_submission)
    
    db.session.commit()

    return redirect(url_for("inserimento", id = id_gara))


@app.route("/richiedi_gara", methods = ["GET", "POST"])
@login_required
def richiedi_gara():
    if current_user.ruolo < 0:
        abort(403)

    form = RequestForm()

    if form.validate_on_submit():
        mistake = request_find_mistake(form)
        if mistake is not None:
            title = "Richiedi un allenamento" if form.is_allenamento.data and current_user.ruolo == 0 else "Fissa un allenamento" if form.is_allenamento.data else "Richiedi una gara" if current_user.ruolo == 0 else "Fissa una gara"
            return render_template("richiedi_gara.html", title = title, form = form, error_message = mistake)
        try:
            new_gara = Gara(
                titolo = form.titolo.data,
                unix_start = italian_to_unix(form.datetime_start.data) if form.start_manuale.data is False else None,
                start_manuale = form.start_manuale.data,
                stato = 0 if current_user.ruolo == 0 else 1,
                richiedente_id = current_user.id,
                is_allenamento = form.is_allenamento.data,
                is_pubblica = not form.is_privata.data,
                is_modificabile_da_richiedente = True,
                durata = form.durata.data,
                n = form.n.data,
                fine_incremento = form.fine_incremento.data,
                tempo_jolly = form.tempo_jolly.data,
                bonus_risposte_json = f"[{form.bonus_risposte_string.data.replace(' ', '')}]",
                bonus_fullato_json = f"[{form.bonus_fullato_string.data.replace(' ', '')}]",
                minuti_oscuri = form.minuti_oscuri.data,
                top_n_squadre_nascoste = form.top_n_squadre_nascoste.data
            )

            for problema in form.problemi.data:
                new_problema = Problema(
                    titolo = problema["titolo"],
                    risultato = problema["risultato"],
                    gara = new_gara
                )
                db.session.add(new_problema)

            for squadra in form.squadre.data:
                new_squadra = Squadra(
                    nome = squadra["nome"],
                    gara = new_gara,
                    is_ospite = squadra["is_ospite"],
                    identificativo_squadra = ''.join(random.choices(string.ascii_uppercase, k = 6)),
                    codice_accesso_squadra = ''.join(random.choices(string.digits, k = 6)),
                    bonus_punti = 0,
                    # TODO: capire se servono i seguenti due
                    ha_fullato = False,
                    bonus_full = 0
                )
                db.session.add(new_squadra)

            usernames_controllanti = [username.strip() for username in str(form.user_controllanti_string.data or "").split(",") if username.strip() != ""]
            if usernames_controllanti:
                for username in usernames_controllanti:
                    user = User.query.filter(User.username == username).first()
                    new_gara.user_controllanti.append(user)
                    new_gara.user_spettatori.append(user)
            if current_user.username not in usernames_controllanti:
                new_gara.user_controllanti.append(current_user)
                new_gara.user_spettatori.append(current_user)

            if form.is_privata.data:
                usernames_spettatori = [username.strip() for username in str(form.user_spettatori_string.data or "").split(",") if username.strip() != ""]
                if usernames_spettatori:
                    for username in usernames_spettatori:
                        if username in usernames_controllanti or username == current_user.username: # già gestito
                            continue
                        user = User.query.filter(User.username == username).first()
                        new_gara.user_spettatori.append(user)


            db.session.add(new_gara)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            title = "Richiedi un allenamento" if form.is_allenamento.data and current_user.ruolo == 0 else "Fissa un allenamento" if form.is_allenamento.data else "Richiedi una gara" if current_user.ruolo == 0 else "Fissa una gara"
            return render_template("richiedi_gara.html", title = title, form = form, error_message = str(e))

        return redirect(url_for("richiesta_effettuata", tipo = "allenamento" if form.is_allenamento.data else "gara"))

    title = "Richiedi un allenamento" if form.is_allenamento.data and current_user.ruolo == 0 else "Fissa un allenamento" if form.is_allenamento.data else "Richiedi una gara" if current_user.ruolo == 0 else "Fissa una gara"
    return render_template("richiedi_gara.html", title = title, form = form)

@app.route("/richiesta_effettuata")
def richiesta_effettuata():
    tipo = request.args.get("tipo")
    h1_testo = ""
    h2_testo = "Aspetta che un admin convalidi la tua richiesta" if current_user.ruolo == 0 else ""
    if tipo == "gara":
        h1_testo = "Gara richiesta" if current_user.ruolo == 0 else "Gara fissata"
    elif tipo == "allenamento":
        h1_testo = "Allenamento richiesto" if current_user.ruolo == 0 else "Allenamento fissato"
    else:
        return redirect(url_for("index"))

    return render_template("richiesta_effettuata.html", title = "Richiesta effettuata", h1_testo = h1_testo, h2_testo = h2_testo)



@app.route("/register", methods = ["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username = form.username.data).first():
            flash(f"Username {form.username.data} già in uso. Scegline un altro.", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(email = form.email.data).first():
            flash(f"Email {form.email.data} già in uso. Scegline un'altra.", "danger")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        new_user = User(nome = form.nome.data, cognome = form.cognome.data, email = form.email.data, username = form.username.data, hashed_password = hashed_password, ruolo = -1)
        db.session.add(new_user)
        db.session.commit()

        flash(f"Richiesta la creazione dell'account {form.username.data} inviata. Un admin la approverà quanto prima.", "success")
        return redirect(url_for("index"))
    return render_template("register.html", title = "Richiedi un account", form = form)

@app.route("/login", methods = ["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash(f"Effettuato l'accesso come {current_user.username}", "success")
        return redirect(url_for("area_riservata"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()

        if not(user and bcrypt.check_password_hash(user.hashed_password, form.password.data)):
            flash(f"Username e/o password non validi", "danger")
            return render_template("login.html", title = "Login", form = form)

        if user.ruolo == -2:
            flash(f"Accesso negato: sei stato bannato da Jeiquarta. Se pensi che sia un errore, contatta un admin", "danger")
            return render_template("login.html", title = "Login", form = form)

        if user.ruolo == -1:
            flash(f"Accesso negato: la richiesta di creazione del tuo account deve prima essere approvata da un admin", "danger")
            return render_template("login.html", title = "Login", form = form)
        
        login_user(user, remember = form.remember.data)
        flash(f"Login effettuato come {form.username.data}", "success")
        return redirect(url_for("area_riservata"))

    return render_template("login.html", title = "Login", form = form)

@app.route("/logout")
def logout():
    logout_user()
    flash("Disconnessione dall'account effettuata con successo", "success")
    return redirect(url_for("index"))


@app.route("/area_riservata")
@login_required
def area_riservata():
    return render_template("area_riservata.html", title = "Area riservata", ruolo_text = ruoli_text_dict.get(current_user.ruolo, "Ruolo sconosciuto"))
