from flask import Blueprint

visual = Blueprint('visual', __name__, url_prefix='/visual')

from . import routes