import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))

rand_string = "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
)


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or rand_string
    SQLALCHEMY_DATABASE_URI = "mysql://b7732efb8cd816:f8ce8f73@us-cdbr-iron-east-04.cleardb.net/heroku_fc83e429e10d4a9"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 3
