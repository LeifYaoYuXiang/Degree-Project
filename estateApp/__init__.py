#encoding:utf-8
import time
from datetime import timedelta

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from estateApp.config import Config


def get_timestamp():
    return int(time.time())


app = Flask(__name__)
app.config.from_object(Config)

app.jinja_env.globals['timestamp'] = get_timestamp


db = SQLAlchemy(app)
from estateApp import routes, models
