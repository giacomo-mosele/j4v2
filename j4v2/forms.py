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
    class Meta:
        csrf = False

    titolo = StringField("Titolo")
    risultato = IntegerField("Risultato", validators = [DataRequired(), NumberRange(min = 0, max = 9999)])

class SquadraForm(FlaskForm):
    class Meta:
        csrf = False

    nome = StringField("Nome squadra")
    is_ospite = BooleanField("Ospite")

class RequestForm(FlaskForm):
    is_allenamento = BooleanField("Allenamento")

    titolo = StringField("Titolo della gara", validators = [DataRequired()])
    start_manuale = BooleanField("Avvio manuale")
    datetime_start = DateTimeLocalField("Data e ora di inizio della gara", format="%Y-%m-%dT%H:%M", validators = [DataRequired()])
    durata = IntegerField("Durata (in minuti)", validators = [DataRequired(), NumberRange(min = 1)])
    n = IntegerField("n =", validators = [DataRequired(), NumberRange(min = 0)])
    fine_incremento = IntegerField("Minuti di incremento automatico", validators = [DataRequired(), NumberRange(min = 0)])
    tempo_jolly = IntegerField("Minuti per la scelta del jolly", validators = [DataRequired(), NumberRange(min = 1)])
    bonus_risposte_string = StringField("Bonus velocità (inserire i valori separati da virgola, ad esempio \"15,10,5\")")
    bonus_fullato_string = StringField("Bonus per chi fulla (inserire i valori separati da virgola, ad esempio \"100,80,60\")")
    minuti_oscuri = IntegerField("Minuti a classifica oscurata", validators = [DataRequired(), NumberRange(min = 0)])
    top_n_squadre_nascoste = IntegerField("Squadre nascoste a fine gara", validators = [DataRequired(), NumberRange(min=0)])

    problemi = FieldList(FormField(ProblemForm), min_entries = 1, label = "Problemi (lascia i titoli vuoti per generarli automaticamente)")
    squadre = FieldList(FormField(SquadraForm), min_entries = 1, label = "Inserisci i nomi delle squadre che parteciperanno")

    user_controllanti_string = StringField("Username degli utenti non admin che (oltre a te) controlleranno la gara (separati da virgola)")

    is_privata = BooleanField("Gara privata")
    user_spettatori_string = StringField("Username degli utenti non admin che (oltre a te e a coloro specificati sopra) potranno vedere la gara (separati da virgola)")

    submit = SubmitField("")

    def _is_user_request_role(self):
        try:
            if not current_user.is_authenticated:
                return False
            return current_user.ruolo <= 0
        except Exception:
            return False

    def _apply_training_labels(self):
        is_user_request = self._is_user_request_role()

        if self.is_allenamento.data:
            self.titolo.label.text = "Titolo dell'allenamento"
            self.datetime_start.label.text = "Data e ora di inizio dell'allenamento"
            self.top_n_squadre_nascoste.label.text = "Partecipanti nascosti a fine allenamento"
            self.user_controllanti_string.label.text = "Username degli utenti non admin che (oltre a te) controlleranno l'allenamento (separati da virgola)"
            self.is_privata.label.text = "Allenamento privato"
            self.user_spettatori_string.label.text = "Username degli utenti non admin che (oltre a te e a coloro specificati sopra) potranno vedere l'allenamento (separati da virgola)"
            if is_user_request:
                self.submit.label.text = "Richiedi l'allenamento"
            else:
                self.submit.label.text = "Fissa l'allenamento"
        else:
            self.titolo.label.text = "Titolo della gara"
            self.datetime_start.label.text = "Data e ora di inizio della gara"
            self.top_n_squadre_nascoste.label.text = "Numero di squadre nascoste a fine gara"
            self.user_controllanti_string.label.text = "Username degli utenti non admin che (oltre a te) controlleranno la gara (separati da virgola)"
            self.is_privata.label.text = "Gara privata"
            self.user_spettatori_string.label.text = "Username degli utenti non admin che (oltre a te e a coloro specificati sopra) potranno vedere la gara (separati da virgola)"
            if is_user_request:
                self.submit.label.text = "Richiedi la gara"
            else:
                self.submit.label.text = "Fissa la gara"

        # aggiorna anche le etichette di eventuali campi generati da WTForms
        # senza toccare testi fuori da questa pagina
        if hasattr(self, "n"):
            self.n.label.text = "n ="
        if hasattr(self, "fine_incremento"):
            self.fine_incremento.label.text = "Minuti di incremento automatico"
        if hasattr(self, "tempo_jolly"):
            self.tempo_jolly.label.text = "Minuti per la scelta del jolly"
        if hasattr(self, "bonus_risposte_string"):
            self.bonus_risposte_string.label.text = "Bonus velocità (inserire i valori separati da virgola, ad esempio \"15,10,5\")"
        if hasattr(self, "bonus_fullato_string"):
            self.bonus_fullato_string.label.text = "Bonus per chi fulla (inserire i valori separati da virgola, ad esempio \"100,80,60\")"
        if hasattr(self, "minuti_oscuri"):
            self.minuti_oscuri.label.text = "Minuti a classifica oscurata"

    def process(self, formdata = None, obj = None, data = None, extra_filters = None):
        if formdata is not None and hasattr(formdata, "get"):
            is_allenamento = formdata.get("is_allenamento") in ("y", "yes", "true", "on", "1", True)
            if is_allenamento:
                formdata = formdata.copy()
                for field_name in ["n", "fine_incremento", "top_n_squadre_nascoste"]:
                    if formdata.get(field_name) in (None, ""):
                        formdata.setlist(field_name, ["0"])
                for field_name in ["bonus_risposte_string", "bonus_fullato_string"]:
                    if formdata.get(field_name) in (None, ""):
                        formdata.setlist(field_name, [""])

        super().process(formdata = formdata, obj = obj, data = data, extra_filters = extra_filters)

    def validate(self, extra_validators = None):
        if self.is_allenamento.data:
            for field_name in ["n", "fine_incremento", "top_n_squadre_nascoste"]:
                field = getattr(self, field_name)
                field.data = 0
                field.raw_data = ["0"]
                field.validators = []
                field.flags.required = False

            self.minuti_oscuri.data = 0
            self.minuti_oscuri.raw_data = ["0"]
            self.minuti_oscuri.validators = [NumberRange(min = 0)]
            self.minuti_oscuri.flags.required = False

            self.bonus_risposte_string.data = ""
            self.bonus_fullato_string.data = ""
        else:
            self.n.validators = [DataRequired(), NumberRange(min = 0)]
            self.fine_incremento.validators = [DataRequired(), NumberRange(min = 0)]
            self.top_n_squadre_nascoste.validators = [DataRequired(), NumberRange(min = 0)]
            self.minuti_oscuri.validators = [DataRequired(), NumberRange(min = 0)]
            self.n.flags.required = True
            self.fine_incremento.flags.required = True
            self.top_n_squadre_nascoste.flags.required = True
            self.minuti_oscuri.flags.required = True

        if self.start_manuale.data:
            self.datetime_start.validators = []
            self.datetime_start.flags.required = False
        else:
            self.datetime_start.validators = [DataRequired()]
            self.datetime_start.flags.required = True

        self._apply_training_labels()
        return super().validate(extra_validators)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_training_labels()