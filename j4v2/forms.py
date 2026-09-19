from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

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