from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

# Путь к корню проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from app.models import User

@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from app import routes, models


@app.route('/static/posts/<filename>')
def custom_static_post(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'posts'), filename)