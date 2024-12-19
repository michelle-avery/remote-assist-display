from flask import Blueprint

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard", template_folder="templates")

from . import views
