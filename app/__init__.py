from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from config import Config
from scouting_report import create_dash_app

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"

dash_app = create_dash_app(app)


from app import routes, models

if __name__ == "__main__":
    dash_app.run_server(debug=True)
