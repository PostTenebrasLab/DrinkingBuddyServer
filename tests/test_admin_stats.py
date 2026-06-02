from datetime import datetime

from ptl_buddy_server.models import db


def _complete(txn):
    """Mark a transaction as completed (canceled_date set = finalized sale)."""
    txn.canceled_date = datetime(2024, 1, 15, 13, 0, 0)
    db.session.commit()


def test_stats_empty_db(client):
    r = client.get('/admin/stats')
    assert r.status_code == 200


def test_stats_with_completed_transaction(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats')
    assert r.status_code == 200


def test_stats_rows_all(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows')
    assert r.status_code == 200


def test_stats_rows_search_match(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?q=Cola')
    assert r.status_code == 200


def test_stats_rows_search_no_match(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?q=NoSuchItem')
    assert r.status_code == 200


def test_stats_rows_category_filter_match(client, transaction, category):
    _complete(transaction)
    r = client.get(f'/admin/stats/rows?has_cat_filter=1&category_id={category.id}')
    assert r.status_code == 200


def test_stats_rows_category_filter_empty_selection_returns_empty(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?has_cat_filter=1')
    assert r.status_code == 200


def test_stats_rows_date_filter_in_range(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?date_from=2024-01-01&date_to=2024-12-31')
    assert r.status_code == 200


def test_stats_rows_date_filter_out_of_range(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?date_from=2023-01-01&date_to=2023-12-31')
    assert r.status_code == 200


def test_stats_rows_sort_revenue_asc(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?sort=revenue&dir=asc')
    assert r.status_code == 200


def test_stats_rows_sort_name(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?sort=name&dir=asc')
    assert r.status_code == 200


def test_stats_rows_sort_unknown_defaults_to_qty(client, transaction):
    _complete(transaction)
    r = client.get('/admin/stats/rows?sort=invalid')
    assert r.status_code == 200


def test_stats_item_id_999_excluded(client, transaction, category):
    from ptl_buddy_server.models import Item, Transaction
    special = Item(id=999, name='Reserved', quantity=0, price=0, category_id=category.id)
    db.session.add(special)
    db.session.commit()
    special_txn = Transaction(
        date=datetime(2024, 1, 15, 12, 0, 0),
        user_id=transaction.user_id,
        quantity=1,
        price_per_item=0,
        element_id=999,
        canceled_date=datetime(2024, 1, 15, 13, 0, 0),
    )
    db.session.add(special_txn)
    db.session.commit()
    r = client.get('/admin/stats/rows')
    assert r.status_code == 200
    assert b'Reserved' not in r.data
