import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))

rand_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or rand_string 
    SQLALCHEMY_DATABASE_URI = "mysql://bc401521a801de:76a77075@us-cdbr-iron-east-05.cleardb.net/heroku_17955da1986c614"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
