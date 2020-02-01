import os
import random
import string

basedir = os.path.abspath(os.path.dirname(__file__))

rand_string = "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(10)
)


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or rand_string
    SQLALCHEMY_DATABASE_URI = "postgres://grlmzqfyszpebe:ef5a0d0f4e94dfd29cc0aa10141705313de934a6baf16341db6c3509a3837b64@ec2-54-92-174-171.compute-1.amazonaws.com:5432/d6ing6qh2i3ncc"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 3
