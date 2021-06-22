from datetime import timedelta

from flask import session

from estateApp import app
from estateApp import routes


if __name__ == "__main__":
    app.permanent_session_lifetime = timedelta(days=7)
    app.run(threaded=True)