import logging
import os

from flask import Blueprint
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

logging.basicConfig(level=logging.WARNING)

_dbpath = os.environ.get('DB_PATH', 'sqlite:////data/drinkingBuddy.db')
_engine = create_engine(_dbpath)
_Session = scoped_session(sessionmaker(bind=_engine))

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.teardown_request
def shutdown_session(exception=None):
    _Session.remove()
