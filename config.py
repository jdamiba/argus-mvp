import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))

rand_string = "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
)


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or rand_string
    SQLALCHEMY_DATABASE_URI = "sqlite:///development.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 3
