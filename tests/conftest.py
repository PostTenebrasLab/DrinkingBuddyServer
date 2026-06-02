from datetime import datetime

import pytest
from flask import Flask

from ptl_buddy_server.admin import admin_bp
from ptl_buddy_server.models import Base, Card, Category, Item, Transaction, User, db


@pytest.fixture()
def app(tmp_path):
    test_app = Flask('ptl_buddy_server')
    test_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'SQLALCHEMY_ENGINES': {'default': f'sqlite:///{tmp_path}/db.sqlite'},
    })
    db.init_app(test_app)
    test_app.register_blueprint(admin_bp)
    with test_app.app_context():
        Base.metadata.create_all(db.engines['default'])
        yield test_app


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['admin_user'] = 'testadmin'
        yield c


@pytest.fixture()
def category(app):
    cat = Category(name='Beverages')
    db.session.add(cat)
    db.session.commit()
    return cat


@pytest.fixture()
def item(app, category):
    it = Item(
        name='Cola',
        quantity=10,
        minquantity=2,
        price=150,
        barcode='12345',
        category_id=category.id,
    )
    db.session.add(it)
    db.session.commit()
    return it


@pytest.fixture()
def user(app):
    u = User(name='Alice', balance=1000, type=1)
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def transaction(app, user, item):
    txn = Transaction(
        date=datetime(2024, 1, 15, 12, 0, 0),
        user_id=user.id,
        quantity=2,
        price_per_item=150,
        element_id=item.id,
        canceled_date=None,
    )
    db.session.add(txn)
    db.session.commit()
    return txn
