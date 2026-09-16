from j4v2 import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    nome = db.Column(db.String(32), nullable = False)
    cognome = db.Column(db.String(32), nullable = False)
    email = db.Column(db.String(64), unique = True, nullable = False)
    username = db.Column(db.String(32), unique = True, nullable = False)
    ruolo = db.Column(db.String(16), nullable = True)
    hashed_password = db.Column(db.String(32), nullable = False)

    def __repr__(self):
        return f"User({self.username})"