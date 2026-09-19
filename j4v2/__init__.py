from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///j4v2.db"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Per accedere all'area riservata è necessario accedere"
login_manager.login_message_category = "info"

from j4v2 import routes