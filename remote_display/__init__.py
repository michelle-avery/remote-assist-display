from flask import Blueprint

bp = Blueprint("remote_display", __name__, url_prefix="/")

from . import views
