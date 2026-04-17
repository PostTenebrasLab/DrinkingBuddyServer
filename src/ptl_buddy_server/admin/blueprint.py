from flask import Blueprint

from ..models import db


def _Session():
    return db.session

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
