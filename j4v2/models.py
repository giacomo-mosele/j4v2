from j4v2 import db, login_manager
from flask_login import UserMixin
import ast

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Relationship many-to-many tra gare e utenti che possono accedere al pannello di controllo
gara_controllo = db.Table(
    "gara_controllo",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", name = "fk_gara_controllo_user"), primary_key = True),
    db.Column("gara_id", db.Integer, db.ForeignKey("gara.id", name = "fk_gara_controllo_gara"), primary_key = True)
)

gara_spettatori = db.Table(
    "gara_spettatori",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id", name = "fk_gara_spettatori_user"), primary_key = True),
    db.Column("gara_id", db.Integer, db.ForeignKey("gara.id", name = "fk_gara_spettatori_gara"), primary_key = True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(32), nullable = False)
    cognome = db.Column(db.String(32), nullable = False)
    email = db.Column(db.String(64), unique = True, nullable = False)
    username = db.Column(db.String(32), unique = True, nullable = False)
    ruolo = db.Column(db.Integer, nullable = True) # 0 = user, 1 = admin, 2 = developer; -1 = da approvare, -2 = bannato
    hashed_password = db.Column(db.String(32), nullable = False)

    gare_richieste = db.relationship("Gara", backref = "richiedente", lazy = True)

    gare_controllate = db.relationship(
        "Gara",
        secondary = gara_controllo,
        backref = db.backref("user_controllanti", lazy = True),
        lazy = True
    )

    gare_spettate = db.relationship(
        "Gara",
        secondary = gara_spettatori,
        backref = db.backref("user_spettatori", lazy = True),
        lazy = True
    )

    def __repr__(self):
        return f"User({self.username})"

class Gara(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    titolo = db.Column(db.String(64), nullable = False)
    unix_start = db.Column(db.BigInteger, nullable = False)

    stato = db.Column(db.Integer, nullable = False) # 0 = richiesta, 1 = inserita, 2 = in corso, 3 = terminata
    richiedente_id = db.Column(db.Integer, db.ForeignKey("user.id", name = "fk_gara_richiedente"), nullable = True) # nullable per gli user cancellati
    
    is_allenamento = db.Column(db.Boolean, nullable = False)
    is_pubblica = db.Column(db.Boolean, nullable = False)
    is_modificabile_da_richiedente = db.Column(db.Boolean, nullable = False, default = True)

    durata = db.Column(db.Integer, nullable = False) # in secondi
    n = db.Column(db.Integer, nullable = False)
    fine_incremento = db.Column(db.Integer, nullable = False)
    tempo_jolly = db.Column(db.Integer, nullable = False)
    bonus_risposte_json = db.Column(db.String(16), nullable = False) # non un problema, è un soft limit. dovrebbe comunque bastare fino a 5 bonus
    bonus_fullato_json = db.Column(db.String(16), nullable = False) # vedi sopra
    minuti_oscuri = db.Column(db.Integer, nullable = False)
    top_n_squadre_nascoste = db.Column(db.Integer, nullable = False)

    problemi = db.relationship("Problema", backref = "gara", lazy = True)
    squadre = db.relationship("Squadra", backref = "gara", lazy = True)
    submissions = db.relationship("Submission", backref = "gara", lazy = True)

    @property
    def bonus_risposte(self):
        return ast.literal_eval(self.bonus_risposte_json)
    @property
    def numero_bonus_risposte(self):
        return len(self.bonus_risposte)
    @property
    def bonus_fullato(self):
        return ast.literal_eval(self.bonus_fullato_json)
    @property
    def numero_bonus_fullato(self):
        return len(self.bonus_fullato)

    @property
    def numero_problemi(self):
        return len(self.problemi)
    @property
    def numero_squadre(self):
        return len(self.squadre)
    @property
    def numero_ospiti(self):
        return len([s for s in self.squadre if s.is_ospite])

    @property
    def numero_full(self):
        return len([s for s in self.squadre if s.ha_fullato])

    def __repr__(self):
        return f"Gara({self.titolo})"

class Problema(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    titolo = db.Column(db.String(64), nullable = False)
    risultato = db.Column(db.Integer, nullable = False)
    gara_id = db.Column(db.Integer, db.ForeignKey("gara.id", name = "fk_problema_gara"), nullable = False)

    submissions = db.relationship("Submission", backref = "problema", lazy = True)

    valore_attuale = db.Column(db.Integer, nullable = False)

    @property
    def numero_risoluzioni(self):
        return len([s for s in self.submissions if s.is_corretta])

    def __repr__(self):
        return f"Problema({self.titolo})"

class Squadra(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(64), nullable = False)
    gara_id = db.Column(db.Integer, db.ForeignKey("gara.id", name = "fk_squadra_gara"), nullable = False)
    email = db.Column(db.String(64), nullable = True)

    is_ospite = db.Column(db.Boolean, nullable = False, default = False)

    identificativo_squadra = db.Column(db.String(6), nullable = True) # ABCXYZ
    codice_accesso_squadra = db.Column(db.String(6), nullable = True) # 123456

    submissions = db.relationship("Submission", backref = "squadra", lazy = True)
    jolly_id = db.Column(db.Integer, db.ForeignKey("problema.id", name = "fk_squadra_jolly"), nullable = True)

    bonus_punti = db.Column(db.Integer, nullable = False, default = 0)
    ha_fullato = db.Column(db.Boolean, nullable = False, default = False)
    bonus_full = db.Column(db.Integer, nullable = False, default = 0)

    def __repr__(self):
        return f"Squadra({self.nome}) per {self.gara}"

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    gara_id = db.Column(db.Integer, db.ForeignKey("gara.id", name = "fk_submission_gara"), nullable = False)
    squadra_id = db.Column(db.Integer, db.ForeignKey("squadra.id", name = "fk_submission_squadra"), nullable = False)
    problema_id = db.Column(db.Integer, db.ForeignKey("problema.id", name = "fk_submission_problema"), nullable = False)

    unix_time = db.Column(db.BigInteger, nullable = False)
    risultato = db.Column(db.Integer, nullable = False)
    is_corretta = db.Column(db.Boolean, nullable = False)
    bonus_associato = db.Column(db.Integer, nullable = False)
    stato_jolly = db.Column(db.Integer, nullable = False) # 0 = non jolly, 1 = jolly piazzato prima, -1 = jolly piazzato dopo

    is_enabled = db.Column(db.Boolean, nullable = False, default = True)

    def __repr__(self):
        return f"Submission({self.squadra}, {self.problema}, {self.risultato})"
