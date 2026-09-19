from flask import render_template, redirect, url_for, flash, abort, send_from_directory, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from j4v2 import app, db, bcrypt
from j4v2.models import *
from j4v2.forms import LoginForm, RegistrationForm

ruoli_text_dict = {
    -2: "Sei stato bannato da Jeiquarta. Se pensi che sia un errore, contatta un admin",
    -1: "La richiesta di creazione del tuo account è in attesa di essere approvata da un admin",
    0: "Ruolo: User",
    1: "Ruolo: Admin",
    2: "Ruolo: Developer"
}

@app.route("/")
def index():
    return redirect(url_for("calendario"))

@app.route("/calendario")
def calendario():
    return render_template("calendario.html", title = "Calendario")

@app.route("/archivio_gare")
def archivio_gare():
    return render_template("archivio_gare.html", title = "Archivio gare")



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
    return render_template("area_riservata.html", title = "Area riservata", ruolo_text = ruoli_text_dict[current_user.ruolo])