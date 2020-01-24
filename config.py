import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'mysql://bc401521a801de:76a77075@us-cdbr-iron-east-05.cleardb.net/heroku_17955da1986c614'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
