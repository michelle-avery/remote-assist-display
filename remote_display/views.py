from . import bp
from flask import redirect, url_for

@bp.route("/")
def index():
    return redirect(url_for("config.config"))
