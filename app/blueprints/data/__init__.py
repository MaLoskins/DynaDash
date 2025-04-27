from flask import Blueprint

data = Blueprint('data', __name__, url_prefix='/data')

from . import routes