from datetime import datetime, timezone

from flask import render_template, redirect, url_for, flash, abort, send_from_directory, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from j4v2 import app, db, bcrypt
from j4v2.models import *
from j4v2.forms import LoginForm, RegistrationForm, RequestForm
from j4v2.utils import *

import random
import string

@app.before_request
def aggiorna_database():
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


@app.route("/")
def index():
    return redirect(url_for("calendario"))

@app.route("/calendario")
def calendario():
    gare_in_corso = Gara.query.filter(Gara.stato == 2).all()
    gare_prossime = Gara.query.filter(Gara.stato == 1).all()
    return render_template("calendario.html", title = "Calendario", gare_in_corso = gare_in_corso, gare_prossime = gare_prossime)

@app.route("/archivio_gare")
def archivio_gare():
    return render_template("archivio_gare.html", title = "Archivio gare")

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