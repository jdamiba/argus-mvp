from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
import os
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

if not flask_server.debug:
    if flask_server.config["MAIL_SERVER"]:
        auth = None
        if flask_server.config["MAIL_USERNAME"] or flask_server.config["MAIL_PASSWORD"]:
            auth = (
                flask_server.config["MAIL_USERNAME"],
                flask_server.config["MAIL_PASSWORD"],
            )
        secure = None
        if flask_server.config["MAIL_USE_TLS"]:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(
                flask_server.config["MAIL_SERVER"],
                flask_server.config["MAIL_PORT"],
            ),
            fromaddr="no-reply@" + flask_server.config["MAIL_SERVER"],
            toaddrs=flask_server.config["ADMINS"],
            subject="Microblog Failure",
            credentials=auth,
            secure=secure,
        )
        mail_handler.setLevel(logging.ERROR)
        flask_server.logger.addHandler(mail_handler)

    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler(
        "logs/microblog.log", maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    flask_server.logger.addHandler(file_handler)

    flask_server.logger.setLevel(logging.INFO)
    flask_server.logger.info("Microblog startup")
