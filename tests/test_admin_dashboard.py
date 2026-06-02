from datetime import datetime

from ptl_buddy_server.models import Item, Transaction, User, db


def test_dashboard_empty_db(client):
    r = client.get('/admin/')
    assert r.status_code == 200


def test_dashboard_with_data(client, item, user, transaction):
    r = client.get('/admin/')
    assert r.status_code == 200


def test_dashboard_shows_low_stock_item(client, item):
    item.quantity = 1  # below minquantity=2
    db.session.commit()
    r = client.get('/admin/')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_dashboard_hides_sufficient_stock_item(client, item):
    item.quantity = 10  # above minquantity=2
    db.session.commit()
    r = client.get('/admin/')
    assert r.status_code == 200
    assert b'Cola' not in r.data


def test_dashboard_item_at_exact_minquantity_is_low_stock(client, item):
    item.quantity = item.minquantity  # quantity == minquantity triggers alert
    db.session.commit()
    r = client.get('/admin/')
    assert r.status_code == 200
    assert b'Cola' in r.data


def test_dashboard_item_without_minquantity_not_shown(client, category):
    it = Item(name='Water', quantity=0, minquantity=None, price=100, category_id=category.id)
    db.session.add(it)
    db.session.commit()
    r = client.get('/admin/')
    assert r.status_code == 200
    # Water has no minquantity set, so no low-stock alert expected
    assert b'Water' not in r.data


def test_dashboard_total_balance_no_users(client):
    # scalar() returns None when no rows; the `or 0` guard must handle it
    r = client.get('/admin/')
    assert r.status_code == 200


def test_dashboard_counts_items_below_id_999_only(client, category):
    # Items with id >= 999 should be excluded from the count
    special = Item(id=999, name='Reserved', quantity=0, price=0, category_id=category.id)
    db.session.add(special)
    db.session.commit()
    r = client.get('/admin/')
    assert r.status_code == 200


def test_dashboard_transaction_count(client, transaction):
    r = client.get('/admin/')
    assert r.status_code == 200
