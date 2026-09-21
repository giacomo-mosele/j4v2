from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, DateTimeLocalField, IntegerField, PasswordField, BooleanField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

class RegistrationForm(FlaskForm):
    nome = StringField("Nome", validators = [DataRequired()])
    cognome = StringField("Cognome", validators = [DataRequired()])
    email = StringField("Email", validators = [DataRequired(), Email()])
    username = StringField("Username (3-16 caratteri)", validators = [DataRequired(), Length(min = 3, max = 16)])
    password = PasswordField("Password (8-64 caratteri)", validators = [DataRequired(), Length(min = 8, max = 64)])
    confirm_password = PasswordField("Conferma password", validators = [DataRequired(), Length(min = 8, max = 64), EqualTo("password")])
    submit = SubmitField("Richiedi un account")

class LoginForm(FlaskForm):
    username = StringField("Username", validators = [DataRequired()])
    password = PasswordField("Password", validators = [DataRequired()])
    remember = BooleanField("Ricordami")
    submit = SubmitField("Login")


class ProblemForm(FlaskForm):
    titolo = StringField("Titolo")
    risultato = IntegerField("Risultato", validators = [DataRequired(), NumberRange(min = 0, max = 9999)])

class SquadraForm(FlaskForm):
    nome = StringField("Nome squadra")
    is_ospite = BooleanField("Ospite")

class RequestForm(FlaskForm):
    titolo = StringField("Titolo della gara", validators = [DataRequired()])
    start_manuale = BooleanField("Avvio manuale")
    datetime_start = DateTimeLocalField("Data e ora di inizio della gara", format="%Y-%m-%dT%H:%M", validators = [DataRequired()])
    durata = IntegerField("Durata (in minuti)", validators = [DataRequired(), NumberRange(min = 1)])
    n = IntegerField("n =", validators = [DataRequired(), NumberRange(min = 1)])
    fine_incremento = IntegerField("Minuti di incremento automatico", validators = [DataRequired(), NumberRange(min = 1)])
    tempo_jolly = IntegerField("Minuti per la scelta del jolly", validators = [DataRequired(), NumberRange(min = 1)])
    bonus_risposte_string = StringField("Bonus velocità (inserire i valori separati da virgola, ad esempio \"15,10,5\")")
    bonus_fullato_string = StringField("Bonus per chi fulla (inserire i valori separati da virgola, ad esempio \"100,80,60\")")
    minuti_oscuri = IntegerField("Minuti a classifica oscurata", validators = [DataRequired(), NumberRange(min = 0)])
    top_n_squadre_nascoste = IntegerField("Squadre nascoste a fine gara", validators = [DataRequired(), NumberRange(min=0)])

    problemi = FieldList(FormField(ProblemForm), min_entries = 1, label = "Problemi (lascia i titoli vuoti per generarli automaticamente)")
    squadre = FieldList(FormField(SquadraForm), min_entries = 1, label = "Inserisci i nomi delle squadre che parteciperanno")

    is_privata = BooleanField("Gara privata")

    user_controllanti_string = StringField("Username degli utenti non admin che (oltre a te) controlleranno la gara (separati da virgola)")
    user_spettatori_string = StringField("Username degli utenti non admin che (oltre a te e a coloro specificati sopra) potranno vedere la gara (separati da virgola)")

    submit = SubmitField("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user.is_authenticated and current_user.ruolo <= 0:
            self.submit.label.text = "Richiedi la gara"
        else:
            self.submit.label.text = "Fissa la gara"