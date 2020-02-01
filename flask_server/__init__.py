from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from config import Config
from scouting_report import create_dash_app

flask_server = Flask(__name__)
flask_server.config.from_object(Config)
db = SQLAlchemy(flask_server)
migrate = Migrate(flask_server, db)
login = LoginManager(flask_server)
login.login_view = "login"

dash_app = create_dash_app(flask_server)


from flask_server import routes, models, errors

if __name__ == "__main__":
    dash_app.run_server(debug=True)

