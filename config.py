import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))

rand_string = "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
)


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or rand_string
    SQLALCHEMY_DATABASE_URI = "mysql://b9dd0c01a98391:e7f33b31@us-cdbr-iron-east-04.cleardb.net/heroku_a9e966c60e99e3b"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE=3600
    SQLALCHEMY_POOL_TIMEOUT=20
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    ADMINS = ["jdamiba@gmail.com"]
    POSTS_PER_PAGE = 3
